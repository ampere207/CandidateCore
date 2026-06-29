class CandidateCoreException(Exception):
    """Base exception for all errors inside CandidateCore engine."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class AdapterException(CandidateCoreException):
    """Raised when an adapter fails to parse or detect input data formats."""
    pass

class ValidationException(CandidateCoreException):
    """Raised when schema validation constraints are violated."""
    pass

class NormalizationException(CandidateCoreException):
    """Raised when an error occurs during value standardizations (e.g. invalid date formats)."""
    pass

class MergeException(CandidateCoreException):
    """Raised during merging or identity resolution conflict execution."""
    pass

class ConfidenceException(CandidateCoreException):
    """Raised when confidence score calculation fails."""
    pass

class ProvenanceException(CandidateCoreException):
    """Raised when tracking metadata/lineage encounters structural issues."""
    pass

class ProjectionException(CandidateCoreException):
    """Raised when projection schema mappings fail validation checks."""
    pass

class EnrichmentException(CandidateCoreException):
    """Raised during semantic parsing or external enrichments."""
    pass

class PipelineException(CandidateCoreException):
    """General error indicating a pipeline run stage failed."""
    pass
