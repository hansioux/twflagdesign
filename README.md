# TW Flag Design (台灣國旗設計同好會)

## 主旨

**台灣國旗設計同好會**：你若是有設計台灣國旗ê想法，請來作伙分享、見學、鑑賞、討論逐家ê創造力！傳設計圖ê時陣請選一个適合ê分類。佇這个社團分享ê圖會使用「CC 版權：姓名標示＋非商業性＋仝款方式分享」授權。若想beh使無仝ê授權請自己註明。

This community is devoted to sharing designs of a future Taiwan/Formosan National flag. We encourage members to share, critique, discuss each other's designs or designs made in the past by those who blazed the trail of Taiwan Independence. Please submit your design to the appropriate category. Designs shared in this forum default to the CC BY-NC-SA license. If you want a separate license, please disclose it when you upload your designs.

**台灣國旗設計同好會**： 沒事就想設計台灣國旗的同好們，一起來分享、觀摩、鑑賞、討論大家的創意！ 請將設計分享到合適的分類裡。 在此分享設計的圖以「CC 版權：姓名標示＋非商業性＋相同方式分享」授權。若想以不同授權分享請自行註明。

## Getting Started

### Prerequisites
- Python 3.12+
- Google Cloud Project credentials (client ID/secret)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `start_app_cred.sh` (or create a `.env` file):
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `SECRET_KEY`

### Running the Application

To start the application with Gunicorn:

```bash
./start_app_cred.sh
```

The application will be available at `http://localhost:8000`.
# twflagdesign
