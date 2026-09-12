"""Local LLM benchmark dataset (spec section 7).

10 cases spanning the categories the build spec lists. Where the text is a
real, well-known public abstract, `source` names the concrete paper so the
provenance is checkable. Domain-specific manufacturing/battery cases where
no single canonical public abstract fits the exact test category are
clearly marked `source="synthetic"` — constructed by this project as a
representative test case, never presented as a real paper (spec section 7:
"개인/회사 기밀자료를 절대 사용하지 않는다"; this project also never
fabricates a citation, so a synthetic case is labeled as such rather than
attributed to an invented paper).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    category: str
    title: str
    abstract: str
    language: str = "en"
    source: str = "synthetic"


CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="industrial-ai-classification",
        category="Industrial AI classification",
        title="Attention Is All You Need",
        abstract=(
            "The dominant sequence transduction models are based on complex recurrent or "
            "convolutional neural networks that include an encoder and a decoder. We propose "
            "a new simple network architecture, the Transformer, based solely on attention "
            "mechanisms, dispensing with recurrence and convolutions entirely. Experiments on "
            "two machine translation tasks show these models to be superior in quality while "
            "being more parallelizable and requiring significantly less time to train."
        ),
        source="arXiv:1706.03762 (Vaswani et al., 2017)",
    ),
    BenchmarkCase(
        id="battery-manufacturing-classification",
        category="Battery Manufacturing classification",
        title="Deep Learning-Based Defect Detection for Lithium-Ion Battery Electrode Coating",
        abstract=(
            "We present a convolutional neural network approach for detecting surface defects "
            "on lithium-ion battery electrode coatings during the slot-die coating process. "
            "The model is trained on line-scan camera images captured on a pilot coating line "
            "and classifies streaks, pinholes, and agglomerates in real time, aiming to reduce "
            "scrap rate in cell manufacturing."
        ),
        source="synthetic",
    ),
    BenchmarkCase(
        id="keyword-extraction",
        category="Technical keyword extraction",
        title="An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        abstract=(
            "While the Transformer architecture has become the de-facto standard for natural "
            "language processing tasks, its applications to computer vision remain limited. We "
            "show that this reliance on CNNs is not necessary and a pure transformer applied "
            "directly to sequences of image patches can perform very well on image "
            "classification tasks, attaining excellent results while requiring substantially "
            "fewer computational resources to train."
        ),
        source="arXiv:2010.11929 (Dosovitskiy et al., 2020)",
    ),
    BenchmarkCase(
        id="korean-technical-summary",
        category="Korean technical summarization",
        title="Vision Transformer for Industrial Surface Defect Inspection",
        abstract=(
            "Surface defect inspection is a critical quality control step in manufacturing. "
            "We adapt a vision transformer pretrained on natural images to industrial surface "
            "defect datasets via transfer learning, achieving higher accuracy than CNN "
            "baselines on scratches, dents, and coating unevenness, while requiring fewer "
            "labeled training examples. A limitation is increased inference latency compared "
            "to lightweight CNNs, which constrains use on low-power edge devices."
        ),
        source="synthetic",
    ),
    BenchmarkCase(
        id="english-technical-summary",
        category="English technical summarization",
        title="Attention Is All You Need",
        abstract=(
            "The dominant sequence transduction models are based on complex recurrent or "
            "convolutional neural networks that include an encoder and a decoder. We propose "
            "a new simple network architecture, the Transformer, based solely on attention "
            "mechanisms, dispensing with recurrence and convolutions entirely. Experiments on "
            "two machine translation tasks show these models to be superior in quality while "
            "being more parallelizable and requiring significantly less time to train. Our "
            "model achieves 28.4 BLEU on the WMT 2014 English-to-German task, improving over "
            "the existing best results by over 2 BLEU."
        ),
        source="arXiv:1706.03762 (Vaswani et al., 2017)",
    ),
    BenchmarkCase(
        id="predictive-maintenance-classification",
        category="Predictive Maintenance classification",
        title="Remaining Useful Life Estimation for Rotating Machinery Using LSTM Networks",
        abstract=(
            "We propose an LSTM-based approach for estimating the remaining useful life of "
            "rotating machinery bearings from vibration sensor time series. Evaluated on the "
            "NASA C-MAPSS and IMS bearing datasets, the model outperforms traditional "
            "degradation-curve fitting methods, enabling condition-based maintenance "
            "scheduling instead of fixed-interval replacement."
        ),
        source="synthetic",
    ),
    BenchmarkCase(
        id="anomaly-detection-classification",
        category="Anomaly Detection classification",
        title="Unsupervised Anomaly Detection in Multivariate Time Series via Transformer Reconstruction",
        abstract=(
            "We propose a transformer-based autoencoder for unsupervised anomaly detection in "
            "multivariate industrial sensor time series. The model learns to reconstruct "
            "normal operating patterns and flags anomalies via reconstruction error, achieving "
            "competitive F1 scores on public server-machine and water-treatment benchmark "
            "datasets without requiring labeled anomalies for training."
        ),
        source="synthetic",
    ),
    BenchmarkCase(
        id="battery-relevance-evaluation",
        category="Battery relevance evaluation",
        title="Machine Vibration Diagnosis for Steel Rolling Mill Motors Using Deep Learning",
        abstract=(
            "We propose a deep learning approach for fault diagnosis of rolling mill drive "
            "motors in steel manufacturing using vibration sensor data, achieving 96% accuracy "
            "on a real industrial dataset. The proposed sensor fusion and fault classification "
            "pipeline generalizes to other rotating equipment with similar vibration "
            "signatures."
        ),
        source="synthetic",
    ),
    BenchmarkCase(
        id="cross-industry-transfer-reasoning",
        category="Cross-industry transfer reasoning",
        title="Wafer Map Defect Pattern Classification Using Convolutional Neural Networks",
        abstract=(
            "We present a CNN-based classifier for identifying spatial defect patterns "
            "(e.g., ring, scratch, donut) on semiconductor wafer maps, trained on the public "
            "WM-811K dataset. The model achieves high accuracy in distinguishing "
            "process-induced defect signatures from random yield loss, supporting root-cause "
            "analysis for fab equipment."
        ),
        source="synthetic (WM-811K dataset is real and public)",
    ),
    BenchmarkCase(
        id="research-question-generation",
        category="Research question generation",
        title="Physics-Informed Neural Networks for Battery Thermal Runaway Prediction",
        abstract=(
            "We integrate governing heat-transfer equations into a neural network's loss "
            "function to predict thermal runaway onset in lithium-ion battery cells from "
            "limited sensor data. The physics-informed model requires less training data than "
            "a purely data-driven baseline and produces physically consistent temperature "
            "predictions, though validation is currently limited to single-cell laboratory "
            "conditions."
        ),
        source="synthetic",
    ),
]


def get_case(case_id: str) -> BenchmarkCase | None:
    return next((c for c in CASES if c.id == case_id), None)


def categories() -> list[str]:
    return [c.category for c in CASES]
