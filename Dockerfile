FROM wigglybot/wigglybot-docker

COPY app /app
CMD ["./wait-for", "eventstore:2113", "--", "python", "component/cron_app.py"]