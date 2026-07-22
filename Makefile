.PHONY: install dev dashboard supervisor check status clean

install:
	pip install -r requirements.txt
	playwright install chromium

dev:
	python dashboard/app.py

supervisor:
	python supervisor.py

check:
	python main.py check

status:
	python main.py status

post:
	python main.py post -t $(TARGET) --title "$(TITLE)" --content "$(CONTENT)"

dashboard:
	python dashboard/app.py

logs:
	tail -f logs/*.log

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf logs/*.log
