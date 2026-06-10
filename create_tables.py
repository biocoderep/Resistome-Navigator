from backend.database.session import engine
from backend.database.base import Base
from backend.models.sample import Sample
from backend.models.batch import Batch, CohortResult
from backend.models.sample_file import SampleFile
from backend.models.amr_gene import AmrGene
from backend.models.amr_hit import AmrHit
from backend.models.analysis_job import AnalysisJob
from backend.models.genome_validation import Assembly

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
