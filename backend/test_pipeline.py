"""Quick test: langdetect + ML layer verification"""
import ml_classifier
ml_classifier.init()  # load trained model

from moderator import _detect_language, _ml_classify

tests = [
    ("You are killing it, great work!",               "Safe"),
    ("Tu bewakoof hai, dimag nahi hai tera.",          "Toxic"),
    ("Bhai aaj ka din bahut acha tha, maza aa gaya!", "Safe"),
    ("Ek baar aur kiya toh I swear main chup nahi rahunga.", "Risky"),
    ("I will find you and make you pay for this.",    "Toxic"),
    ("The vaccines have microchips, share this now!", "Toxic"),
    ("Go kill yourself, nobody wants you here.",      "Toxic"),
    ("Nice job genius. Totally not sarcastic.",       "Risky"),
    ("Women don't belong in tech, they ruin everything.", "Toxic"),
    ("Congratulations on the promotion, well deserved!", "Safe"),
]

print("=== LANGUAGE DETECTION + ML LAYER ===")
print(f"  {'Result':5} {'Expected':5} {'Conf':5} {'Language':12} Text")
print("  " + "-" * 72)

correct = 0
for t, expected in tests:
    lang = _detect_language(t)
    ml = _ml_classify(t)
    cat = ml["category"]
    conf = ml["confidence"]
    ok = "OK  " if cat == expected else "MISS"
    if cat == expected:
        correct += 1
    print(f"  [{ok}] {cat:5} {conf:3}%  {lang:12}  {t[:50]}")

m = ml_classifier.get_metrics()
print()
print(f"Test accuracy : {correct}/{len(tests)} ({correct/len(tests):.0%})")
print(f"Model         : {m.get('model_type')}")
print(f"CV Accuracy   : {m.get('cv_accuracy_mean', 0):.1%}")
print(f"Train Accuracy: {m.get('training_accuracy', 0):.0%}")
print(f"Examples      : {m.get('training_examples')}")
print()
print("=== LANGUAGE DETECTION ONLY ===")
hinglish_tests = [
    "Bhai yaar kya hua aaj?",
    "I swear yeh toh bahut bura tha.",
    "Tu dimag mat kha mera.",
    "This movie is literally fire, must watch!",
    "Mujhe nahi pata kya ho raha hai.",
]
for t in hinglish_tests:
    lang = _detect_language(t)
    print(f"  {lang:12} | {t}")
