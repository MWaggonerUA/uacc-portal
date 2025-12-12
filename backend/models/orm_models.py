"""
ORM models for database tables.

This module defines SQLAlchemy ORM models for all dataset types.
Each model includes metadata fields for tracking uploads.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Index
from sqlalchemy.sql import func
from backend.services.db import Base


class BudgetRecord(Base):
    """ORM model for RLOGX budgets data."""
    __tablename__ = 'budgets'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Upload metadata
    upload_timestamp = Column(DateTime, nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    upload_batch_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Data columns (from database schema)
    grant_id = Column(String(255), nullable=True)
    project_title = Column(String(255), nullable=True)
    grant_number = Column(String(255), nullable=True)
    core_project_number = Column(String(255), nullable=True)
    funding_source = Column(String(255), nullable=True)
    peer_review_type = Column(String(255), nullable=True)
    grant_start_date = Column(Date, nullable=True)
    grant_end_date = Column(Date, nullable=True)
    grant_direct_cost = Column(Float, nullable=True)
    grant_indirect_cost = Column(Float, nullable=True)
    grant_total = Column(Integer, nullable=True)
    prime_award_id = Column(String(255), nullable=True)
    prime_agency_name = Column(String(255), nullable=True)
    subcontract = Column(Integer, nullable=True)
    multi_pi = Column(Float, nullable=True)
    multi_investigator = Column(Integer, nullable=True)
    nce = Column(Integer, nullable=True)
    r01_like = Column(Integer, nullable=True)
    project_link = Column(String(255), nullable=True)
    allocation_of = Column(String(255), nullable=True)
    budget_period_id = Column(Float, nullable=True)
    period_grant_number = Column(String(255), nullable=True)
    period = Column(Float, nullable=True)
    period_start_date = Column(Date, nullable=True)
    period_end_date = Column(Date, nullable=True)
    period_directs = Column(Float, nullable=True)
    period_indirect = Column(Float, nullable=True)
    period_total = Column(Integer, nullable=True)
    ccsg_fund = Column(Integer, nullable=True)
    linked_investigators = Column(String(255), nullable=True)
    research_programs = Column(String(255), nullable=True)
    cancer_relevance = Column(Float, nullable=True)
    justification = Column(String(255), nullable=True)
    rlogx_uid = Column(String(255), nullable=True)
    flagged_for_review = Column(Integer, nullable=True)
    import_source = Column(String(255), nullable=True)
    workspace_status = Column(String(255), nullable=True)
    imported_pis = Column(String(255), nullable=True)
    imported_pi_ids = Column(String(255), nullable=True)
    last_updated = Column(Date, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_budgets_grant_id', 'grant_id'),
        Index('idx_budgets_rlogx_uid', 'rlogx_uid'),
        Index('idx_budgets_upload_timestamp', 'upload_timestamp'),
    )


class FundingRecord(Base):
    """ORM model for RLOGX funding data."""
    __tablename__ = 'funding'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Upload metadata
    upload_timestamp = Column(DateTime, nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    upload_batch_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Data columns (from database schema)
    project_status = Column(String(255), nullable=True)
    project_id = Column(String(255), nullable=True)  # Changed from Integer to String to support alphanumeric IDs like "SMOKEFUND001"
    project_uid = Column(String(255), nullable=True)
    fund_ws_id = Column(Integer, nullable=True)
    fiscal_year = Column(Float, nullable=True)
    project_title = Column(String(255), nullable=True)
    grant_number = Column(String(255), nullable=True)
    fund_source = Column(String(255), nullable=True)
    project_begin = Column(Date, nullable=True)
    project_end = Column(Date, nullable=True)
    project_status_id = Column(Integer, nullable=True)
    project_summary = Column(String(255), nullable=True)
    master_fund = Column(Integer, nullable=True)
    allocation_of = Column(Float, nullable=True)
    training_project = Column(Integer, nullable=True)
    indirect_cost = Column(Float, nullable=True)
    direct_cost = Column(Float, nullable=True)
    cancer_relevance_percentage = Column(Float, nullable=True)
    peer_review_type_id = Column(Integer, nullable=True)
    fund_review_status_id = Column(Integer, nullable=True)
    batch_id = Column(String(255), nullable=True)
    import_source = Column(String(255), nullable=True)
    import_file = Column(String(255), nullable=True)
    imported_pi = Column(String(255), nullable=True)
    imported_pi_id = Column(String(255), nullable=True)
    project_ts = Column(String(255), nullable=True)
    is_subcontract = Column(Integer, nullable=True)
    multi_pi = Column(Float, nullable=True)
    multi_investigator = Column(Integer, nullable=True)
    no_cost_ext = Column(Integer, nullable=True)
    r01_like = Column(Integer, nullable=True)
    is_ccsg_fund = Column(Integer, nullable=True)
    prime_award_id = Column(String(255), nullable=True)
    prime_agency_name = Column(String(255), nullable=True)
    funding_ic = Column(Text, nullable=True)
    restricted_funds = Column(Float, nullable=True)
    internal_project_id = Column(String(255), nullable=True)
    project_sort = Column(Integer, nullable=True)
    copied_from = Column(Text, nullable=True)
    inv_cancer_relevance_percentage = Column(Text, nullable=True)
    inv_justification = Column(String(255), nullable=True)
    inv_notes = Column(String(255), nullable=True)
    inv_verified_by = Column(Text, nullable=True)
    inv_verified_ts = Column(Text, nullable=True)
    orig_project_id = Column(Text, nullable=True)
    is_core = Column(Integer, nullable=True)
    flag_for_review = Column(Integer, nullable=True)
    core_project_num = Column(String(255), nullable=True)
    project_url = Column(String(255), nullable=True)
    is_supplement = Column(Float, nullable=True)
    include_in_roi = Column(Integer, nullable=True)
    view_budget_begin = Column(String(255), nullable=True)
    view_budget_end = Column(String(255), nullable=True)
    unobligated_balance = Column(Float, nullable=True)
    fund_code = Column(Text, nullable=True)
    grant_type = Column(String(255), nullable=True)
    grant_activity = Column(Text, nullable=True)
    is_clinical_trial = Column(Float, nullable=True)
    grant_purpose = Column(Text, nullable=True)
    public_health_relevance = Column(String(255), nullable=True)
    modified_date = Column(String(255), nullable=True)
    modified_by = Column(Float, nullable=True)
    peer_review_type = Column(String(255), nullable=True)
    investigators = Column(String(255), nullable=True)
    investigators_principal = Column(String(255), nullable=True)
    member_types = Column(String(255), nullable=True)
    total_allocs = Column(Float, nullable=True)
    list_programs = Column(String(255), nullable=True)
    this_count = Column(Float, nullable=True)
    investigators_other = Column(Text, nullable=True)
    total_budgets = Column(Float, nullable=True)
    subcontract_in_direct_cost = Column(Text, nullable=True)
    subcontract_in_indirect_cost = Column(Text, nullable=True)
    subcontract_out_direct_cost = Column(Text, nullable=True)
    subcontract_out_indirect_cost = Column(Text, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_funding_project_id', 'project_id'),
        Index('idx_funding_project_uid', 'project_uid'),
        Index('idx_funding_upload_timestamp', 'upload_timestamp'),
    )


class ILabsRecord(Base):
    """ORM model for iLabs data."""
    __tablename__ = 'ilabs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Upload metadata
    upload_timestamp = Column(DateTime, nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    source_tab_name = Column(String(255), nullable=True)  # Excel tab name
    upload_batch_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Data columns (from database schema)
    user_login_email = Column(String(255), nullable=True)
    pi_email = Column(String(255), nullable=True)
    financial_contact_email = Column(String(255), nullable=True)
    service_id = Column(String(255), nullable=True)
    service_type = Column(String(255), nullable=True)
    asset_id = Column(Float, nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_title = Column(String(255), nullable=True)
    customer_lab = Column(String(255), nullable=True)
    customer_department = Column(String(255), nullable=True)
    customer_institute = Column(String(255), nullable=True)
    charge_name = Column(String(255), nullable=True)
    notes = Column(String(255), nullable=True)
    payment_information = Column(String(255), nullable=True)
    custom_field = Column(String(255), nullable=True)
    expense_object_code_revenue_object_code = Column(String(255), nullable=True)
    account_subaccount = Column(String(255), nullable=True)
    orgin_code = Column(String(255), nullable=True)
    status = Column(String(255), nullable=True)
    billing_status = Column(String(255), nullable=True)
    unit_of_measure = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    conversion = Column(Float, nullable=True)
    updated_quantity = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    price_type = Column(String(255), nullable=True)
    creation_date = Column(DateTime, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    billing_date = Column(DateTime, nullable=True)
    date_file_sent_to_erp = Column(DateTime, nullable=True)
    billing_event_end_date = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=True)
    core_name = Column(String(255), nullable=True)
    invoice_num = Column(String(255), nullable=True)
    no_charge_justification = Column(String(255), nullable=True)
    ad_hoc_charge_justification = Column(Text, nullable=True)
    organization_name = Column(String(255), nullable=True)
    company_organization_name = Column(String(255), nullable=True)
    charge_id = Column(Float, nullable=True)
    reviewed = Column(String(255), nullable=True)
    center = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    usage_type = Column(String(255), nullable=True)
    vendor = Column(Text, nullable=True)
    unspsc_code = Column(Text, nullable=True)
    unspsc_name = Column(Text, nullable=True)
    facility_catalog_number = Column(Text, nullable=True)
    central_catalog_number = Column(String(255), nullable=True)
    core_id = Column(Float, nullable=True)
    ck_fund_type = Column(String(255), nullable=True)
    final_status = Column(String(255), nullable=True)
    billing_core = Column(String(255), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_ilabs_charge_id', 'charge_id'),
        Index('idx_ilabs_invoice_num', 'invoice_num'),
        Index('idx_ilabs_user_login_email', 'user_login_email'),
        Index('idx_ilabs_pi_email', 'pi_email'),
        Index('idx_ilabs_upload_timestamp', 'upload_timestamp'),
        Index('idx_ilabs_source_tab_name', 'source_tab_name'),
    )


class MembershipRecord(Base):
    """ORM model for RLOGX membership data."""
    __tablename__ = 'membership'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Upload metadata
    upload_timestamp = Column(DateTime, nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    upload_batch_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Data columns (from database schema)
    member_status = Column(String(255), nullable=True)
    rlogx_id = Column(Integer, nullable=True)
    rlogx_uid = Column(String(255), nullable=True)
    internal_id = Column(Float, nullable=True)
    last_name = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    middle_name = Column(String(255), nullable=True)
    credentials = Column(String(255), nullable=True)
    preferred_name = Column(String(255), nullable=True)
    maiden_name = Column(String(255), nullable=True)
    salutation = Column(Text, nullable=True)
    suffix = Column(String(255), nullable=True)
    email_address = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    mobile = Column(Text, nullable=True)
    fax = Column(Text, nullable=True)
    orcid = Column(String(255), nullable=True)
    author_names = Column(String(255), nullable=True)
    date_added_to_rlogx = Column(Date, nullable=True)
    member_id = Column(Integer, nullable=True)
    ccm_type_code = Column(Text, nullable=True)
    program_name = Column(String(255), nullable=True)
    research_interests = Column(Text, nullable=True)
    campus = Column(Text, nullable=True)
    race = Column(String(255), nullable=True)
    ethnicity = Column(String(255), nullable=True)
    gender = Column(String(255), nullable=True)
    nih_reporter_id = Column(String(255), nullable=True)
    phone_number = Column(Text, nullable=True)
    fax_number = Column(Text, nullable=True)
    ccsg_role = Column(Text, nullable=True)
    nih_bibliography_url = Column(String(255), nullable=True)
    ccm_start_date = Column(Date, nullable=True)
    ccm_end_date = Column(Date, nullable=True)
    current_research_programs = Column(String(255), nullable=True)
    program_start_date = Column(Date, nullable=True)
    program_end_date = Column(Date, nullable=True)
    program_member_type = Column(String(255), nullable=True)
    senior_leadership_title = Column(String(255), nullable=True)
    program_history = Column(String(255), nullable=True)
    rank_primary_appointment = Column(String(255), nullable=True)
    department_primary_appointment = Column(String(255), nullable=True)
    division_primary_appointment = Column(Text, nullable=True)
    school_primary_appointment = Column(String(255), nullable=True)
    rank_secondary_appointment = Column(Text, nullable=True)
    department_secondary_appointment = Column(Text, nullable=True)
    division_secondary_appointment = Column(Text, nullable=True)
    school_secondary_appointment = Column(Text, nullable=True)
    themes = Column(Text, nullable=True)
    net_id = Column(String(255), nullable=True)
    four_year_term = Column(String(255), nullable=True)
    full = Column(String(255), nullable=True)
    associate = Column(String(255), nullable=True)
    last_first_name = Column(String(255), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_membership_rlogx_id', 'rlogx_id'),
        Index('idx_membership_rlogx_uid', 'rlogx_uid'),
        Index('idx_membership_email_address', 'email_address'),
        Index('idx_membership_member_id', 'member_id'),
        Index('idx_membership_program_name', 'program_name'),
        Index('idx_membership_upload_timestamp', 'upload_timestamp'),
    )


class ProposalRecord(Base):
    """ORM model for proposals data."""
    __tablename__ = 'proposals'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Upload metadata
    upload_timestamp = Column(DateTime, nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    upload_batch_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Data columns (from database schema)
    proposal_id = Column(Integer, nullable=True)
    proposal_title = Column(String(255), nullable=True)
    contact_role_description = Column(String(255), nullable=True)
    contact_role_code = Column(String(255), nullable=True)
    total_effort = Column(Float, nullable=True)
    proposal_status = Column(String(255), nullable=True)
    proposal_status_description = Column(String(255), nullable=True)
    multiple_pi_flag = Column(Integer, nullable=True)
    submitted_date = Column(Date, nullable=True)
    lead_investigator_organization_name = Column(String(255), nullable=True)
    lead_investigator_organization_code = Column(String(255), nullable=True)
    lead_investigator_name = Column(String(255), nullable=True)
    requested_start_date = Column(Date, nullable=True)
    requested_end_date = Column(Date, nullable=True)
    total_cost_by_investigator = Column(Float, nullable=True)
    f_a_revenue_percentage_by_investigator_organization = Column(Float, nullable=True)
    total_cost_by_investigator1 = Column(Float, nullable=True)
    indirect_cost_by_investigator_organization = Column(Float, nullable=True)
    direct_cost_by_investigator_organization = Column(Float, nullable=True)
    indirect_cost_by_investigator_organization1 = Column(Float, nullable=True)
    investigator_name = Column(String(255), nullable=True)
    organization_name = Column(String(255), nullable=True)
    organization_code = Column(String(255), nullable=True)
    sponsor_name = Column(String(255), nullable=True)
    lead_investigator_organization_rollup_college_name = Column(String(255), nullable=True)
    college_name = Column(String(255), nullable=True)
    college_code = Column(String(255), nullable=True)
    college_name1 = Column(String(255), nullable=True)
    college_code1 = Column(String(255), nullable=True)
    total_cost = Column(Float, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_proposals_proposal_id', 'proposal_id'),
        Index('idx_proposals_submitted_date', 'submitted_date'),
        Index('idx_proposals_lead_investigator_name', 'lead_investigator_name'),
        Index('idx_proposals_upload_timestamp', 'upload_timestamp'),
    )


class PublicationRecord(Base):
    """ORM model for RLOGX publications data."""
    __tablename__ = 'publications'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Upload metadata
    upload_timestamp = Column(DateTime, nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    upload_batch_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Data columns (from database schema)
    rlogx_link = Column(String(255), nullable=True)
    pubmed_link = Column(String(255), nullable=True)
    publication_id = Column(Integer, nullable=True)
    publication_uid = Column(String(255), nullable=True)
    pubmed_uid = Column(Integer, nullable=True)
    title = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    authors = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    journal = Column(String(255), nullable=True)
    journal_full = Column(String(255), nullable=True)
    volume = Column(String(255), nullable=True)
    issue = Column(String(255), nullable=True)
    pages = Column(String(255), nullable=True)
    pmc_id = Column(String(255), nullable=True)
    nih_ms_id = Column(String(255), nullable=True)
    doi = Column(String(255), nullable=True)
    pub_date = Column(Date, nullable=True)
    pub_year = Column(Integer, nullable=True)
    pubmed_date = Column(Date, nullable=True)
    e_pub_date = Column(String(255), nullable=True)
    print_date = Column(String(255), nullable=True)
    abstract = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    affiliations = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    grants = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    pub_type = Column(String(255), nullable=True)
    pub_ts = Column(String(255), nullable=True)
    pub_first_author = Column(String(255), nullable=True)
    pub_last_author = Column(String(255), nullable=True)
    import_date = Column(String(255), nullable=True)
    issn = Column(String(255), nullable=True)
    essn = Column(String(255), nullable=True)
    cancer_relevance_justification = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    nci_collaboration = Column(Integer, nullable=True)
    peer_reviewed = Column(Integer, nullable=True)
    cancer_relevant = Column(Integer, nullable=True)
    external_collaboration = Column(Integer, nullable=True)
    impact_value = Column(Float, nullable=True)
    max_impact = Column(Float, nullable=True)
    min_impact = Column(Float, nullable=True)
    first_author_is_ccm = Column(Integer, nullable=True)
    last_author_is_ccm = Column(Integer, nullable=True)
    all_ccm_authors_possible_names = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    all_ccm_authors = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    intraprogrammatic = Column(Integer, nullable=True)
    identify_intra_authors = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    intra_authors = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    nci_cc_collaboration = Column(Integer, nullable=True)
    identified_cancer_centers = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    interprogrammatic = Column(Integer, nullable=True)
    identify_inter_authors = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    inter_authors = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    inter_programs = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    leader_reviewed = Column(Text, nullable=True)
    both_in_trainter = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    research_programs = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    author_verification = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    cores_used = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    citation = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    research_program = Column(Text, nullable=True)  # Changed to TEXT to avoid row size limit
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_publications_publication_id', 'publication_id'),
        Index('idx_publications_publication_uid', 'publication_uid'),
        Index('idx_publications_pub_date', 'pub_date'),
        Index('idx_publications_upload_timestamp', 'upload_timestamp'),
    )

