# Güncellenmiş kod: anomaly score'a göre renk bloklarıyla görselleştirme
import json, random, time
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

def gen_authorize(cp_id, idtag):
    return {
        "chargePointId": cp_id,
        "timestamp": time.time(),
        "idTag": idtag,
        "action": "Authorize"
    }

# 1) veri üret
rows = []
cp_ids = ["CP-1","CP-2","CP-3"]
idtags = ["TAG-A","TAG-B","TAG-C","TAG-D","TAG-E"]

for t in range(1000):
    cp = random.choice(cp_ids)
    tag = random.choice(idtags)
    msg = gen_authorize(cp, tag)
    tampered = 1 if random.random() < 0.05 else 0
    if tampered:
        msg["idTag"] = random.choice([x for x in idtags if x != tag])
    rows.append((msg, tampered))

# 2) feature extraction
data = []
labels = []
# naive freq feature
for msg, tam in rows:
    idt = msg["idTag"]
    freq = sum(1 for m,_ in rows if m["idTag"]==idt)
    data.append([freq])
    labels.append(tam)

X = np.array(data)
y = np.array(labels)

# 3) isolation forest
clf = IsolationForest(contamination=0.05, random_state=0)
clf.fit(X)
scores = -clf.decision_function(X)  # yüksek score = anomali

# 4) görselleştir (farklı aralıklarda renk değişimi)
indices = np.arange(len(scores))

# Eşikleri otomatik belirlemek için percentil kullan (33% ve 66%)
p33, p66 = np.percentile(scores, [33, 66])

# Maske tanımları
low_mask   = scores <= p33
mid_mask   = (scores > p33) & (scores <= p66)
high_mask  = scores > p66

plt.figure(figsize=(10,5))

# Her aralığı farklı renk/line style ile çiz (nokta sıralı olsa da bloklar görünür)
plt.plot(indices[low_mask],  scores[low_mask],  marker='o', linestyle='-', label=f'Low (<= {p33:.4f})')
plt.plot(indices[mid_mask],  scores[mid_mask],  marker='o', linestyle='-', label=f'Mid ({p33:.4f} - {p66:.4f})')
plt.plot(indices[high_mask], scores[high_mask], marker='o', linestyle='-', label=f'High (> {p66:.4f})')

# Manipüle edilmiş noktaları siyah X ile üstüne çiz
tampered_idx = np.where(y==1)[0]
plt.scatter(tampered_idx, scores[tampered_idx], marker='x', color='k', s=60, linewidths=1.5, label='tampered (ground truth)')

plt.xlabel('sample index')
plt.ylabel('anomaly score')
plt.title('Anomaly score with color blocks by score range')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
