# Helmet Detection System V0.35

BOS 啟發式自適應推論策略於即時校園安全監控之研究

---

# 專案簡介

Helmet Detection System V0.35 並不是單純的 YOLO 物件偵測展示系統。

本專案的核心目標，是研究：

> 如何在有限計算資源下，動態決定何時值得執行昂貴的深度學習推論。

傳統即時視覺系統通常會：

- 每一幀都執行完整 YOLO 推論
- 持續消耗大量 CPU / GPU 資源
- 造成延遲累積
- 增加邊緣部署成本
- 產生大量重複計算

然而在真實監控場景中，大量連續影格之間其實高度相似。

因此：

> 並不是每一幀都值得花一次完整 YOLO 成本。

本專案重新將即時影像辨識視為：

> 一個「線上排程（Online Scheduling）」與「推論資源管理（Inference Resource Allocation）」問題。

而不是單純的物件偵測問題。

---

# 研究動機

近年來，校園內機車、電動車與微型移動載具數量逐漸增加，但也伴隨：

- 未戴安全帽
- 危險騎乘
- 人車混流
- 違規行為

等校園安全問題。

由於校園道路空間有限，一旦發生事故，未配戴安全帽容易造成嚴重頭部傷害。

目前多數校園安全管理仍依賴：

- 人工巡查
- 保全勸導
- 事後檢舉

這些方式需要大量人力，且難以長時間即時監控。

YOLO 等深度學習模型雖然能應用於科技執法與智慧監控，但其完整推論成本相當高昂。

若對監視器每一幀都執行完整推論，將導致：

- CPU / GPU 資源消耗過高
- 長時間監控成本增加
- 即時性下降
- 邊緣設備難以部署

因此，本研究希望探討：

> 是否能只在「真正值得偵測」的時候，才執行昂貴 YOLO 推論。

---

# 核心概念

本專案將：

| 排程概念 | 視覺系統對應 |
|---|---|
| Job | 影格 / ROI |
| Machine | CPU / GPU Worker |
| 昂貴作業 | 完整 YOLO 推論 |
| Cheap Test | Motion Detection / ROI Analysis |
| Cache | 舊偵測結果重用 |
| Scheduling Policy | 自適應推論決策 |

系統會根據：

- Motion Score
- Cache Age
- ROI 變化
- 場景穩定度
- Detection History

動態決定：

- 是否執行 YOLO
- 是否沿用快取
- 是否強制刷新推論
- 是否跳過低價值影格

---

# 系統架構

```text
Video Input
    ↓
Cheap Feature Layer
(Motion / ROI / Frame Difference)
    ↓
BOS-Inspired Scheduler
    ↓
┌───────────────────────┐
│ 是否執行完整 YOLO ?   │
└───────────────────────┘
     ↓ Yes                  ↓ No
Full YOLO Detect        Reuse Cache
     ↓                      ↓
Helmet Violation Analysis
     ↓
Visualization + Logging
```

---

# 目前功能

## 已完成

- YOLOv8 即時物件偵測
- Motion-based Adaptive Scheduling
- ROI 區域裁切
- Detection Cache 重用
- FPS / Latency 顯示
- 即時視訊與影片輸入
- BOS-inspired 推論排程邏輯

---

# 研究導向功能

本專案主軸並非單純提高辨識率，而是：

- Adaptive Inference
- Online Scheduling
- Resource-aware Vision System
- Edge AI
- 即時推論資源管理

---

# 為什麼使用 BOS 概念？

本專案受到：

> BOS（Bottleneck-Oriented Scheduling）

的概念啟發。

BOS 的核心思想是：

> 系統真正的瓶頸資源，應該被優先分配給最值得的工作。

在本專案中：

- YOLO 被視為昂貴瓶頸資源
- 每一幀影像被視為待處理工作
- Scheduler 負責決定哪些 frame 值得花推論成本

因此系統不再是：

```text
每幀 → YOLO → 輸出
```

而是：

```text
觀察狀態 → 評估 urgency → 動態決策 → 推論
```

---

# 使用技術

## 核心套件

- Python
- Ultralytics YOLOv8
- OpenCV
- NumPy
- PyTorch

---

# 研究目標

本專案主要評估：

- FPS
- Latency
- Tail Latency (P95 / P99)
- Detector Call Ratio
- Compute Cost
- Detection Quality Tradeoff

核心研究問題：

> 是否能在維持合理偵測品質下，大幅降低 YOLO 推論成本？

---

# 未來規劃

## 短期目標

- 安全帽分類器
- 人車配對
- Event-level 違規追蹤
- Replay Simulation

## 長期目標

- 多 Worker 平行推論
- Queue-aware Scheduling
- Budget-aware Inference
- ONNX Runtime 優化
- Edge Deployment
- CPU/GPU Hybrid Scheduling

---

# 適用場景

- 校園安全監控
- 智慧交通分析
- 邊緣 AI 視覺系統
- 即時監控研究
- 推論排程研究
- Resource-aware Vision Systems

---

# 免責聲明

本專案僅作為：

- 學術研究
- 教學實驗
- 系統設計研究

用途使用。

並非正式科技執法系統。

---

# 作者資訊

Chen-Hong  
國立中正大學 電訊傳播研究所  
National Chung Cheng University

GitHub：  
https://github.com/scuranger0625/Helmet-Detection-System
