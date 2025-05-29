.PHONY: all clean

APP=lab5msN3146

all: $(APP)

$(APP): $(APP).py
	python -m PyInstaller --onefile $(APP).py
	mv ./dist/$(APP) ./$(APP)
	rm -rf build
	rm -rf dist
	rm $(APP).spec

clean:
	rm $(APP)
