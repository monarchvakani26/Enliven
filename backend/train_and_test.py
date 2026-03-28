"""Run this script to train the SafeSphere ML classifier."""
import ml_classifier

metrics = ml_classifier.train()
print()
print("=== MODEL TRAINING COMPLETE ===")
print(f"Examples      : {metrics['training_examples']}")
print(f"Train Accuracy: {metrics['training_accuracy']:.1%}")
print(f"CV Accuracy   : {metrics['cv_accuracy_mean']:.1%} +/- {metrics['cv_accuracy_std']:.1%}")
print(f"Model Type    : {metrics['model_type']}")
print()
print("Per-class Metrics:")
for cls, m in metrics["per_class"].items():
    print(f"  {cls:5}: Precision={m['precision']:.0%}  Recall={m['recall']:.0%}  F1={m['f1']:.0%}")

print()
print("=== INFERENCE TESTS ===")
ml_classifier.load()

tests = [
    ("You are killing it! Great work bro!", "Safe"),
    ("I will find you and make you pay.", "Toxic"),
    ("Tu bewakoof hai, dimag nahi hai tera.", "Toxic"),
    ("5G towers were designed to spread the virus!", "Toxic"),
    ("Oh wow nice job genius. Totally not sarcastic.", "Risky"),
    ("Bhai aaj ka din bahut acha tha!", "Safe"),
    ("Go kill yourself, nobody wants you here.", "Toxic"),
    ("Congratulations on the promotion, totally deserved!", "Safe"),
    ("Ek baar aur kiya toh I swear main chup nahi rahunga.", "Risky"),
    ("The vaccines contain microchips to control people!", "Toxic"),
]

correct = 0
for text, expected in tests:
    r = ml_classifier.predict(text)
    ok = r["category"] == expected
    if ok:
        correct += 1
    status = "OK  " if ok else "MISS"
    print(f"  [{status}] {r['category']:5} {r['confidence']:3}% | {text[:55]}")

print(f"\nTest Accuracy: {correct}/{len(tests)} ({correct/len(tests):.0%})")
