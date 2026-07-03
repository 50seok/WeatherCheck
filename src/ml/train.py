"""CLI: 모델 3개(LR/RF/XGB) 비교 리포트 + 최종 모델 pkl 저장.
실행: python -m src.ml.train (project root에서)
"""
import joblib

from src.ml.predict import train_all

MODEL_DIR = "src/ml/models"


def run():
    import os
    os.makedirs(MODEL_DIR, exist_ok=True)
    result = train_all()

    print("=== 회귀: 내일 최고기온 MAE (낮을수록 좋음) ===")
    for name, mae in result["reg_scores"].items():
        print(f"{name}: MAE={mae:.3f}")

    print("\n=== 분류: 내일 비 여부 Accuracy (높을수록 좋음) ===")
    for name, acc in result["clf_scores"].items():
        print(f"{name}: Accuracy={acc:.3f}")

    joblib.dump(result["reg_max"], f"{MODEL_DIR}/best_regressor_max.pkl")
    joblib.dump(result["reg_min"], f"{MODEL_DIR}/best_regressor_min.pkl")
    joblib.dump(result["clf"], f"{MODEL_DIR}/best_classifier.pkl")
    print(
        f"\n최고 모델: 회귀={result['best_reg_name']}(MAE={result['best_mae']:.3f}), "
        f"분류={result['best_clf_name']}(Acc={result['best_acc']:.3f})"
    )
    print(f"-> {MODEL_DIR}/ 에 저장")


if __name__ == "__main__":
    run()
