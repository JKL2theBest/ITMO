from prometheus_client import Counter

NEWS_CREATED_TOTAL = Counter("news_created_total", "Total number of news created")

USERS_REGISTERED_TOTAL = Counter(
    "users_registered_total", "Total number of registered users"
)

NOTIFICATIONS_SENT_TOTAL = Counter(
    "notifications_sent_total", "Total number of email notifications sent", ["type"]
)
