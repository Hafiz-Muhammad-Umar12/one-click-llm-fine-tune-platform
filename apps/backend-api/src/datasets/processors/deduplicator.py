import hashlib
from typing import Dict, Any, Tuple
from datasketch import MinHash
from src.datasets.processors.base import BasePreprocessor

class ExactDeduplicator(BasePreprocessor):
    """
    Performs streaming exact deduplication using SHA256 hashes.
    In a fully distributed environment, the `seen_hashes` set would be a Redis Bloom Filter
    to maintain O(1) memory across billions of rows.
    """
    def __init__(self, target_keys: list[str]):
        self.target_keys = target_keys
        self.seen_hashes = set()
        self.duplicates_removed = 0

    @property
    def name(self) -> str:
        return "exact_deduplicator"

    def _hash_record(self, record: Dict[str, Any]) -> str:
        # Extract content based on keys, sort them to ensure consistent hashing
        content = ""
        for key in sorted(self.target_keys):
            if key in record:
                content += str(record[key])
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def process(self, record: Dict[str, Any]) -> Dict[str, Any]:
        record_hash = self._hash_record(record)
        if record_hash in self.seen_hashes:
            self.duplicates_removed += 1
            return None # Drop record
        
        self.seen_hashes.add(record_hash)
        return record

class MinHashDeduplicator(BasePreprocessor):
    """
    Semantic deduplication using MinHash LSH.
    Identifies records that are structurally similar (e.g., Jaccard similarity > 0.9).
    """
    def __init__(self, target_keys: list[str], threshold: float = 0.9, num_perm: int = 128):
        from datasketch import MinHashLSH
        self.target_keys = target_keys
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.duplicates_removed = 0
        self.record_counter = 0

    @property
    def name(self) -> str:
        return "semantic_deduplicator"

    def process(self, record: Dict[str, Any]) -> Dict[str, Any]:
        content = " ".join([str(record.get(k, "")) for k in self.target_keys]).lower()
        tokens = content.split()
        
        m = MinHash(num_perm=self.num_perm)
        for token in tokens:
            m.update(token.encode('utf8'))
            
        result = self.lsh.query(m)
        if len(result) > 0:
            self.duplicates_removed += 1
            return None # Drop record
            
        self.lsh.insert(str(self.record_counter), m)
        self.record_counter += 1
        return record
