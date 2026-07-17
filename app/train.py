import os
import random
import logging
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
from app.config import MODEL_DIR, BASE_DIR
from app.utils import set_seed

logger = logging.getLogger("app.train")

def run_training():
    logger.info("Starting model training to generate my_model_bce...")

    # Reproducibility
    RANDOM_SEED = 42
    set_seed(RANDOM_SEED)

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Training device: {DEVICE}")

    dataset_path = BASE_DIR / "final_synthetic_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)

    # Prepare dataset
    if "input_text" not in df.columns:
        df["input_text"] = df["permission"].astype(str) + " | " + df["category"].astype(str)

    if "label_float" not in df.columns:
        raise ValueError("Dataset must contain 'label_float' column (0.0/1.0).")

    df["labels"] = df["label_float"].astype(float)
    df = df[["input_text", "permission", "category", "label", "labels", "reason"]]

    # Stratified train/validation split
    train_df, val_df = train_test_split(
        df,
        test_size=0.15,
        random_state=RANDOM_SEED,
        stratify=df["label"]
    )

    # Convert to HF DatasetDict
    dataset = DatasetDict({
        "train": Dataset.from_pandas(train_df.reset_index(drop=True)),
        "validation": Dataset.from_pandas(val_df.reset_index(drop=True))
    })

    MODEL_NAME = "bert-base-uncased"
    logger.info(f"Loading tokenizer {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
        clean_up_tokenization_spaces=True
    )

    def tokenize_fn(batch):
        return tokenizer(
            batch["input_text"],
            padding="max_length",
            truncation=True,
            max_length=128
        )

    logger.info("Tokenizing datasets...")
    tokenized = dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=["input_text", "permission", "category", "label", "reason"]
    )
    tokenized.set_format(
        type="torch",
        columns=["input_ids", "attention_mask", "labels"]
    )

    logger.info("Initializing model...")
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=1)
    model.to(DEVICE)

    # Partial unfreeze (freeze first 10 layers, unfreeze last 2)
    for name, param in model.named_parameters():
        if name.startswith("bert.encoder.layer.") and int(name.split('.')[3]) < 10:
            param.requires_grad = False

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # sklearn metrics for evaluation
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        roc_auc_score,
        brier_score_loss,
        confusion_matrix
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        logits = np.array(logits).reshape(-1)
        probs = 1.0 / (1.0 + np.exp(-logits))
        preds = (probs >= 0.5).astype(int)
        labels = labels.astype(int).reshape(-1)

        results = {
            "accuracy": float(accuracy_score(labels, preds)),
            "precision": float(precision_score(labels, preds, zero_division=0)),
            "recall": float(recall_score(labels, preds, zero_division=0)),
            "f1": float(f1_score(labels, preds, zero_division=0)),
        }

        if len(np.unique(labels)) == 2:
            try:
                results["roc_auc"] = float(roc_auc_score(labels, probs))
            except Exception:
                results["roc_auc"] = float("nan")
        else:
            results["roc_auc"] = float("nan")

        try:
            results["brier"] = float(brier_score_loss(labels, probs))
        except Exception:
            results["brier"] = float("nan")

        tn, fp, fn, tp = confusion_matrix(labels, preds, labels=[0, 1]).ravel()
        results["tp"] = int(tp)
        results["tn"] = int(tn)
        results["fp"] = int(fp)
        results["fn"] = int(fn)

        return results

    logger.info("Setting up trainer...")
    training_args = TrainingArguments(
        output_dir=str(BASE_DIR / "results"),
        num_train_epochs=1,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        fp16=torch.cuda.is_available(),
        report_to="none"
    )

    class BCETrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.get("labels").float().to(model.device)
            inputs = {k: v for k, v in inputs.items() if k != "labels"}
            outputs = model(**inputs)
            logits = outputs.logits.view(-1)
            loss_fct = nn.BCEWithLogitsLoss()
            loss = loss_fct(logits, labels)
            return (loss, outputs) if return_outputs else loss

    trainer = BCETrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("Running training...")
    trainer.train()
    logger.info("Training complete.")

    logger.info(f"Saving model and tokenizer to {MODEL_DIR}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(MODEL_DIR))
    tokenizer.save_pretrained(str(MODEL_DIR))
    logger.info(f"Model saved successfully to {MODEL_DIR}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_training()
