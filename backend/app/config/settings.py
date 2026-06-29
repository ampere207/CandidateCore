from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field(
        "CandidateCore Canonicalization Engine", 
        validation_alias="APP_NAME"
    )
    env: str = Field(
        "development", 
        validation_alias="ENV"
    )
    log_level: str = Field(
        "INFO", 
        validation_alias="LOG_LEVEL"
    )
    api_host: str = Field(
        "0.0.0.0", 
        validation_alias="API_HOST"
    )
    api_port: int = Field(
        8000, 
        validation_alias="API_PORT"
    )

    # Ingestion adapter configurations
    csv_delimiter: str = Field(
        ",", 
        validation_alias="CSV_DELIMITER"
    )
    
    # Adapter priority list for merging conflicts, ordered from least trusted to most trusted
    source_priority_list: str = Field(
        "recruiter_notes,recruiter_csv,resume_pdf,ats_json", 
        validation_alias="SOURCE_PRIORITY_LIST"
    )

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
