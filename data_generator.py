import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

CHANNELS = ["Organic Search", "Paid Search", "Social Media", "Email", "Direct", "Referral"]
CAMPAIGNS = ["Brand Awareness Q1", "Retargeting Spring", "Lead Gen B2B", "Promo Descuentos", "Newsletter Semanal"]

def generate_daily_traffic(days=90):
    dates = [datetime.today() - timedelta(days=i) for i in range(days, 0, -1)]
    records = []
    for date in dates:
        for channel in CHANNELS:
            base = {"Organic Search": 800, "Paid Search": 500, "Social Media": 400,
                    "Email": 200, "Direct": 300, "Referral": 150}[channel]
            trend = 1 + (days - (datetime.today() - date).days) * 0.003
            seasonality = 1 + 0.15 * np.sin(2 * np.pi * date.timetuple().tm_yday / 7)
            sessions = int(base * trend * seasonality * np.random.uniform(0.85, 1.15))
            conv_rate = {"Organic Search": 0.032, "Paid Search": 0.048, "Social Media": 0.021,
                         "Email": 0.065, "Direct": 0.041, "Referral": 0.028}[channel]
            conversions = int(sessions * conv_rate * np.random.uniform(0.9, 1.1))
            revenue = conversions * np.random.uniform(80, 220)
            records.append({
                "date": date.date(),
                "channel": channel,
                "sessions": sessions,
                "conversions": conversions,
                "revenue": round(revenue, 2),
            })
    return pd.DataFrame(records)


def generate_campaigns():
    records = []
    for camp in CAMPAIGNS:
        spend = np.random.uniform(2000, 15000)
        roas = np.random.uniform(1.8, 5.5)
        revenue = spend * roas
        impressions = int(spend * np.random.uniform(80, 200))
        clicks = int(impressions * np.random.uniform(0.02, 0.07))
        conversions = int(clicks * np.random.uniform(0.03, 0.09))
        records.append({
            "campaign": camp,
            "spend": round(spend, 2),
            "revenue": round(revenue, 2),
            "roas": round(roas, 2),
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": round(clicks / impressions * 100, 2),
            "cpc": round(spend / clicks, 2),
        })
    return pd.DataFrame(records)


def generate_funnel():
    stages = ["Visitantes", "Leads", "MQLs", "SQLs", "Clientes"]
    values = [10000, 2800, 980, 420, 160]
    return pd.DataFrame({"stage": stages, "count": values})


def generate_email_metrics(weeks=12):
    records = []
    for i in range(weeks, 0, -1):
        week = datetime.today() - timedelta(weeks=i)
        sent = np.random.randint(8000, 15000)
        open_rate = np.random.uniform(0.18, 0.32)
        ctr = np.random.uniform(0.03, 0.08)
        records.append({
            "week": week.date(),
            "sent": sent,
            "opens": int(sent * open_rate),
            "clicks": int(sent * ctr),
            "open_rate": round(open_rate * 100, 1),
            "ctr": round(ctr * 100, 1),
            "unsubscribes": np.random.randint(10, 60),
        })
    return pd.DataFrame(records)
