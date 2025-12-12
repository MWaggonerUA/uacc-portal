"""
Processor for RLOGX publications dataset.
"""
import logging
import math
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.utils import parse_date
from backend.models.orm_models import PublicationRecord

logger = logging.getLogger(__name__)


class RLOGXPublicationsProcessor(BaseDatasetProcessor):
    """Processor for RLOGX publications data."""
    
    # Mapping from full program names to abbreviations
    PROGRAM_ABBREVIATIONS = {
        'Cancer Biology': 'CBP',
        'Cancer Prevention & Control': 'CPCP',
        'Clinical & Translational Oncology': 'CTOP'
    }
    
    def get_required_columns(self) -> List[str]:
        """Return required columns for publications dataset."""
        return [
            'RLOGX Link', 'publicationID', 'publicationUID', 'title', 'authors',
            'journal', 'journal_full', 'pubDate'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Return optional columns for publications dataset."""
        return [
            'pubmedDate', 'peerReviewed', 'cancerRelevant',
            'externalCollaboration', 'firstAuthorIsCCM', 'lastAuthorIsCCM',
            'intraProgrammatic', 'interProgrammatic', 'NCI CC Collaboration',
            'pmcid', 'abstract', 'grants', 'affiliations',
            'pubFirstAuthor', 'pubLastAuthor', 'impactValue',
            'allCCMAuthors_possibleNames', 'allCCMAuthors', 'researchPrograms',
            'Citation', 'PubMed Link', 'pubmeduid'
        ]
    
    def _normalize_yes_no(self, value: Any) -> int:
        """
        Normalize yes/no values to 1/0.
        
        Handles various formats:
        - "yes"/"no", "Yes"/"No", "YES"/"NO" → 1/0
        - Already coded 1/0 → 1/0
        - Missing/empty values → 0
        
        Args:
            value: Value to normalize
            
        Returns:
            1 if value explicitly indicates "yes", 0 otherwise (including missing values)
        """
        if value is None:
            return 0
        
        # Handle string values
        if isinstance(value, str):
            value = value.strip().lower()
            if not value or value in ('', 'nan', 'none', 'null', 'n/a', 'na'):
                return 0
            # Check for explicit yes values
            if value in ('yes', 'y', '1', 'true', 't'):
                return 1
            # Check for explicit no values
            if value in ('no', 'n', '0', 'false', 'f'):
                return 0
            # For unknown string values, default to 0 (conservative approach)
            # Note: If columns have "yes values only", empty cells are 0, 
            # and any present value should match one of the yes patterns above
            return 0
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            # Check for NaN
            if isinstance(value, float) and math.isnan(value):
                return 0
            # Convert to int: 1 if non-zero, 0 if zero
            return 1 if int(value) != 0 else 0
        
        # Handle boolean values
        if isinstance(value, bool):
            return 1 if value else 0
        
        # For any other type, default to 0
        return 0
    
    def _extract_most_common_program(self, valid_rows: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract the most common research program from the 'researchPrograms' column.
        
        The 'researchPrograms' column can contain comma-separated program names.
        This method finds the most frequently occurring program across all rows
        and returns its abbreviation.
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            Program abbreviation (CBP, CPCP, or CTOP) or None if no programs found
        """
        program_counter = Counter()
        
        for row in valid_rows:
            # Get the researchPrograms value (case-insensitive lookup)
            research_programs = None
            for col_name, value in row.items():
                # Check both exact match and case-insensitive match
                if col_name == 'researchPrograms' or col_name.lower() == 'researchprograms':
                    research_programs = value
                    break
            
            if research_programs is None:
                continue
            
            # Convert to string and handle None/empty
            if not isinstance(research_programs, str):
                if research_programs is None:
                    continue
                research_programs = str(research_programs)
            
            research_programs = research_programs.strip()
            if not research_programs:
                continue
            
            # Split by comma and process each program
            programs = [p.strip() for p in research_programs.split(',')]
            for program in programs:
                if program:
                    program_counter[program] += 1
        
        if not program_counter:
            return None
        
        # Find the most common program
        most_common_program, _ = program_counter.most_common(1)[0]
        
        # Map to abbreviation
        abbreviation = self.PROGRAM_ABBREVIATIONS.get(most_common_program)
        
        if abbreviation:
            self.logger.debug(
                f"Most common research program: '{most_common_program}' → '{abbreviation}' "
                f"(appeared {program_counter[most_common_program]} times)"
            )
        else:
            self.logger.warning(
                f"Most common research program '{most_common_program}' not found in abbreviations map. "
                f"Available programs: {list(self.PROGRAM_ABBREVIATIONS.keys())}"
            )
        
        return abbreviation
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Performs the following transformations:
        - Maps column names from processor format to database format (snake_case)
        - Standardizes date formats for date columns
        - Converts yes/no columns to 1/0
        - Extracts most common research program and adds 'research_program_abbrv' column
        - Handles missing values appropriately
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        # First, determine the most common research program for this batch (file)
        most_common_program_abbrv = self._extract_most_common_program(valid_rows)
        
        transformed_rows = []
        
        # Date columns that need parsing
        date_columns = [
            'pubDate',
            'pubmedDate',
            'ePubDate',
            'printDate'
        ]
        
        # Yes/no columns that need to be converted to 1/0
        yes_no_columns = [
            'cancerRelevant',
            'peerReviewed',
            'intraProgrammatic',
            'interProgrammatic',
            'externalCollaboration',
            'nCICollaboration',
            'firstAuthorIsCCM',
            'lastAuthorIsCCM',
            'NCI CC Collaboration'
        ]
        
        for row in valid_rows:
            transformed_row = {}
            
            # Map all column names and transform values
            for col_name, value in row.items():
                # Map column name to database format (snake_case)
                db_col_name = self._map_column_names(col_name)
                
                # Parse date columns
                if col_name in date_columns:
                    transformed_row[db_col_name] = parse_date(value)
                # Convert yes/no columns to 1/0
                elif col_name in yes_no_columns:
                    transformed_row[db_col_name] = self._normalize_yes_no(value)
                else:
                    # For non-date, non-yes/no columns, preserve the value (already validated)
                    # Convert NaN/None to None for database compatibility
                    if value is None or (isinstance(value, str) and value.strip() == ''):
                        transformed_row[db_col_name] = None
                    else:
                        transformed_row[db_col_name] = value
            
            # Add the research_program_abbrv column to each row
            transformed_row['research_program_abbrv'] = most_common_program_abbrv
            
            transformed_rows.append(transformed_row)
        
        self.logger.debug(f"Transformed {len(transformed_rows)} rows for database insertion")
        return transformed_rows
    
    async def write_to_database(
        self,
        valid_rows: List[Dict[str, Any]],
        db_session: AsyncSession,
        upload_timestamp: str = None,
        source_filename: str = None,
        upload_batch_id: str = None
    ) -> int:
        """
        Write transformed publications data to database.
        
        Args:
            valid_rows: List of transformed row dictionaries (already mapped to database column names)
            db_session: Database session
            upload_timestamp: ISO format timestamp of the upload
            source_filename: Name of the uploaded file
            upload_batch_id: Optional batch ID for grouping related uploads
            
        Returns:
            Number of rows successfully inserted
        """
        if not valid_rows:
            self.logger.warning("No valid rows to insert")
            return 0
        
        # Parse upload_timestamp if it's a string
        if upload_timestamp:
            try:
                if isinstance(upload_timestamp, str):
                    upload_dt = datetime.fromisoformat(upload_timestamp.replace('Z', '+00:00'))
                else:
                    upload_dt = upload_timestamp
            except (ValueError, AttributeError):
                self.logger.warning(f"Could not parse upload_timestamp '{upload_timestamp}', using current time")
                upload_dt = datetime.now()
        else:
            upload_dt = datetime.now()
        
        inserted_count = 0
        
        try:
            for row in valid_rows:
                # Create database record
                record_data = {
                    'upload_timestamp': upload_dt,
                    'source_filename': source_filename or 'unknown',
                    'upload_batch_id': upload_batch_id,
                }
                
                # Add data fields, only including those that match ORM model attributes
                valid_model_attrs = {
                    'rlogx_link', 'pubmed_link', 'publication_id', 'publication_uid',
                    'pubmed_uid', 'title', 'authors', 'journal', 'journal_full',
                    'volume', 'issue', 'pages', 'pmc_id', 'nih_ms_id', 'doi',
                    'pub_date', 'pub_year', 'pubmed_date', 'e_pub_date', 'print_date',
                    'abstract', 'affiliations', 'grants', 'pub_type', 'pub_ts',
                    'pub_first_author', 'pub_last_author', 'import_date', 'issn',
                    'essn', 'cancer_relevance_justification', 'nci_collaboration',
                    'peer_reviewed', 'cancer_relevant', 'external_collaboration',
                    'impact_value', 'max_impact', 'min_impact', 'first_author_is_ccm',
                    'last_author_is_ccm', 'all_ccm_authors_possible_names', 'all_ccm_authors',
                    'intraprogrammatic', 'identify_intra_authors', 'intra_authors',
                    'nci_cc_collaboration', 'identified_cancer_centers', 'interprogrammatic',
                    'identify_inter_authors', 'inter_authors', 'inter_programs',
                    'leader_reviewed', 'both_in_trainter', 'research_programs',
                    'author_verification', 'cores_used', 'citation', 'research_program'
                    # Note: research_program_abbrv is computed during transformation
                    # but not stored in database, so we don't include it here
                }
                
                for key, value in row.items():
                    if key in valid_model_attrs:
                        # Convert date strings to date objects if needed
                        if key in ('pub_date', 'pubmed_date'):
                            if value is None:
                                record_data[key] = None
                            elif isinstance(value, str):
                                try:
                                    record_data[key] = datetime.fromisoformat(value).date()
                                except (ValueError, AttributeError):
                                    self.logger.warning(f"Could not parse date '{value}' for column '{key}', setting to None")
                                    record_data[key] = None
                            else:
                                record_data[key] = value
                        else:
                            record_data[key] = value
                
                # Create and add ORM record
                db_record = PublicationRecord(**record_data)
                db_session.add(db_record)
                inserted_count += 1
            
            # Commit all records
            await db_session.commit()
            self.logger.info(
                f"Successfully inserted {inserted_count} publication record(s) "
                f"(source: {source_filename or 'unknown'}, timestamp: {upload_timestamp})"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error inserting publication records: {e}",
                exc_info=True
            )
            await db_session.rollback()
            raise
        
        return inserted_count

