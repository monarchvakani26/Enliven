"""
SafeSphere AI — Multilingual Sample Comments Dataset
Mix of English, Hindi, Hinglish with Safe / Risky / Toxic labels
"""

SAMPLE_COMMENTS = [
    # ─── SAFE — English ──────────────────────────────────────────────────────
    {"text": "Great work everyone, the team really pulled through!", "expected": "Safe"},
    {"text": "You're absolutely killing it on this project 🔥", "expected": "Safe"},
    {"text": "This is the best product launch we've had in years.", "expected": "Safe"},
    {"text": "I disagree with the policy, but I respect the process.", "expected": "Safe"},
    {"text": "Anyone else obsessed with the new season? It's fire!", "expected": "Safe"},
    {"text": "Congratulations on the promotion, totally deserved! 🎉", "expected": "Safe"},
    {"text": "This debate is getting heated but I love the passion.", "expected": "Safe"},

    # ─── SAFE — Hindi / Hinglish ─────────────────────────────────────────────
    {"text": "Yaar aaj ka din bahut acha tha, maza aa gaya!", "expected": "Safe"},
    {"text": "Bhai tune toh kamaal kar diya aaj!", "expected": "Safe"},
    {"text": "Shukriya dost, teri help ke bina kuch nahi hota.", "expected": "Safe"},
    {"text": "Kal cricket match dekhte hain, bohot mazedaar hoga.", "expected": "Safe"},

    # ─── RISKY — Ambiguous / Sarcastic ──────────────────────────────────────
    {"text": "Oh wow, nice job genius. You've really outdone yourself.", "expected": "Risky"},
    {"text": "Yeah sure, because THAT worked so well last time 🙄", "expected": "Risky"},
    {"text": "Some people just shouldn't be allowed on the internet.", "expected": "Risky"},
    {"text": "I'm not saying he's stupid, but... connect the dots.", "expected": "Risky"},
    {"text": "This government is destroying everything, fight back!", "expected": "Risky"},
    {"text": "Nice job idiot, you broke the whole system again.", "expected": "Risky"},
    {"text": "These politicians are all corrupt, we should do something.", "expected": "Risky"},
    {"text": "Kuch log sirf drama karte hain, koi kaam nahi inhe.", "expected": "Risky"},

    # ─── TOXIC — Threats ─────────────────────────────────────────────────────
    {"text": "I will find you and make you pay for this.", "expected": "Toxic"},
    {"text": "You better watch your back, I know where you live.", "expected": "Toxic"},
    {"text": "Keep talking and I'll destroy your career.", "expected": "Toxic"},
    {"text": "Teri aisi ki taisi kar dunga, samjha kya?", "expected": "Toxic"},

    # ─── TOXIC — Bullying / Harassment ───────────────────────────────────────
    {"text": "You are the dumbest person I've ever seen online.", "expected": "Toxic"},
    {"text": "Tu bewakoof hai, akal nahi hai teri.", "expected": "Toxic"},
    {"text": "Go kill yourself, nobody wants you here.", "expected": "Toxic"},
    {"text": "You're worthless and everyone knows it.", "expected": "Toxic"},
    {"text": "Yeh toh bilkul gadha hai, kuch samajh nahi aata isko.", "expected": "Toxic"},

    # ─── TOXIC — Hate Speech ─────────────────────────────────────────────────
    {"text": "All [group] people are criminals and should be removed.", "expected": "Toxic"},
    {"text": "These [religion] people shouldn't be allowed in our country.", "expected": "Toxic"},
    {"text": "Women don't belong in tech, they ruin everything.", "expected": "Toxic"},

    # ─── TOXIC — Misinformation ──────────────────────────────────────────────
    {"text": "The vaccines contain microchips to track you, don't take them!", "expected": "Toxic"},
    {"text": "5G towers were designed to spread the virus, share this!", "expected": "Toxic"},
    {"text": "The election was completely rigged, the results are fake!", "expected": "Toxic"},

    # ─── MIXED LANGUAGE ──────────────────────────────────────────────────────
    {"text": "Bro this movie is literally fire, must watch karo!", "expected": "Safe"},
    {"text": "Ek baar aur kiya toh I swear main chup nahi rahunga.", "expected": "Risky"},
    {"text": "Yaar ye log toh bakwaas karte hain, ignore kar inhe.", "expected": "Risky"},
]
