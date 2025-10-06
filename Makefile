CHESSDB_PATH = /media/ssd_t7/chessdb/chess-20250608/data
TERARKDBROOT = ../terarkdb
CDBDIRECT_PATH = ../cdbdirect

CXX = g++
CXXFLAGS = -Wall -Wextra -fno-omit-frame-pointer -fno-inline -std=c++17 -O3 -g -march=native
CXXFLAGS += -DCHESSDB_PATH=\"$(CHESSDB_PATH)\"
LDFLAGS = -L$(TERARKDBROOT)/output/lib -L$(CDBDIRECT_PATH) -flto=auto
LIBS = -lcdbdirect -lterarkdb -lterark-zip-r -lboost_fiber -lboost_context -ltcmalloc -pthread -lgcc -lrt -ldl -ltbb -laio -lgomp -lsnappy -llz4 -lz -lbz2 -latomic

SRC_FILE = litrack2dump.cpp
EXE_FILE = litrack2dump
EXT_HEADERS = external/chess.hpp

all: $(EXE_FILE)

$(EXE_FILE): $(SRC_FILE)
	$(CXX) $(CXXFLAGS) -o $(EXE_FILE) $(SRC_FILE) $(LDFLAGS) $(LIBS)

format:
	clang-format -i $(SRC_FILE)
	black litrack2cdb.py litrack.py
	shfmt -w -i 2 do_track.sh

clean:
	rm -f $(EXE_FILE)
