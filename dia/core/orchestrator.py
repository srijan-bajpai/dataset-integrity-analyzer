import os
from .dataset import DatasetRecord
from ..extract.embeddings import FeatureExtractor
from ..analyzers.distribution import DistributionAnalyzer
from ..analyzers.quality import QualityAnalyzer
from ..analyzers.duplicates import DuplicatesAnalyzer
from ..analyzers.diversity import DiversityAnalyzer
from ..analyzers.labels import LabelAuditAnalyzer
from ..scoring.readiness import ReadinessScorer

class DIAOrchestrator:
    """
    Main entry point for running the DIA pipeline.
    """
    def __init__(self, data_dir: str):
        self.dataset = DatasetRecord(data_dir)
        self.aggregate_results = {}
        
    def run_all(self, update_callback=None):
        def notify(msg):
            if update_callback:
                update_callback(msg)
            else:
                print(msg)
                
        notify("Ingesting dataset...")
        df = self.dataset.ingest_folder_per_class()
        
        notify("Extracting embeddings...")
        extractor = FeatureExtractor(df)
        embeddings = extractor.extract("embeddings.npy")
        
        notify("Analyzing Class Distribution...")
        self.aggregate_results['distribution'] = DistributionAnalyzer(df).run()
        
        notify("Analyzing Image Quality...")
        self.aggregate_results['quality'] = QualityAnalyzer(df).run()
        
        notify("Detecting Duplicates...")
        self.aggregate_results['duplicates'] = DuplicatesAnalyzer(df).run()
        
        notify("Measuring Visual Diversity...")
        self.aggregate_results['diversity'] = DiversityAnalyzer(df, embeddings).run()
        
        notify("Auditing Label Consistency...")
        self.aggregate_results['labels'] = LabelAuditAnalyzer(df, embeddings).run()
        
        from ..analyzers.confounds import ConfoundAnalyzer
        notify("Detecting Cross-Dimensional Confounds...")
        self.aggregate_results['confounds'] = ConfoundAnalyzer(df).run()
        
        notify("Computing AI Readiness Score...")
        scorer = ReadinessScorer(self.aggregate_results)
        self.aggregate_results['readiness'] = scorer.compute()
        
        from ..predict.impact import BiasImpactPredictor
        notify("Predicting Bias Impact (C2)...")
        self.aggregate_results['bias_impact'] = BiasImpactPredictor(self.aggregate_results).predict()
        
        from ..recommend.engine import RecommendationEngine
        notify("Generating Recommendations...")
        self.aggregate_results['recommendations'] = RecommendationEngine(self.aggregate_results).generate()
        
        notify("Saving unified dataset record to DB...")
        self.dataset.save_to_sqlite()
        
        return self.aggregate_results, self.dataset.df
