.PHONY: build clean install test

# Detect OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PYTHON := python3
    PIP := pip3
    GRADLEW := ./gradlew
endif
ifeq ($(UNAME_S),Darwin)
    PYTHON := python3
    PIP := pip3
    GRADLEW := ./gradlew
endif
ifeq ($(OS),Windows_NT)
    PYTHON := python
    PIP := pip
    GRADLEW := gradlew.bat
endif

build: build-backend build-gui build-android

build-backend:
	@echo "Building .NET Backend..."
	cd src/MirrorSync.Backend && dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true

build-gui:
	@echo "Building Python GUI..."
	cd gui && $(PYTHON) generate_proto.py
	cd gui && $(PIP) install -r requirements.txt
	cd gui && pyinstaller --onedir --windowed --name MirrorSyncGUI main_window.py

build-android:
	@echo "Building Android Agent..."
	cd android && $(GRADLEW) assembleRelease

clean:
	rm -rf src/MirrorSync.Backend/bin/
	rm -rf src/MirrorSync.Backend/obj/
	rm -rf gui/dist/
	rm -rf gui/build/
	rm -rf android/app/build/

test:
	$(PYTHON) test_system.py

install: build
	@echo "Installation requires Windows environment"