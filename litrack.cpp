#include <chrono>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include "../cdbdirect/cdbdirect.h"
#include "external/chess.hpp"

using namespace chess;

std::vector<std::string> fens;

const int tb_limit = 7;

bool is_pos_in_cdb(std::uintptr_t handle, const Board &board) {
  auto result = cdbdirect_get(handle, board.getFen(false));
  int ply = result[result.size() - 1].second;
  return ply > -2;
}

class MyVisitor : public pgn::Visitor {
public:
  MyVisitor(std::uintptr_t handle) : handle(handle) {}
  virtual ~MyVisitor() {}

  void startPgn() {}

  void header(std::string_view key, std::string_view value) {
    if (key == "FEN") {
      board.setFen(value);
      if (!is_pos_in_cdb(handle, board)) {
        this->skipPgn(true);
        return;
      }
      fen_plus_moves = board.getFen();
    }
  }

  void startMoves() {}

  void move(std::string_view move, std::string_view) {
    Move m = uci::parseSan(board, move, moves);
    if (m == Move::NO_MOVE) {
      this->skipPgn(true);
      return;
    }

    board.makeMove<true>(m);

    Movelist movelist;
    movegen::legalmoves(movelist, board);
    if (movelist.empty() || board.occ().count() <= tb_limit) {
      this->skipPgn(true);
      return;
    }

    if (still_in_cdb) {
      if (is_pos_in_cdb(handle, board)) {
        fen_plus_moves = board.getFen();
      } else {
        still_in_cdb = false;
        fen_plus_moves += " moves " + uci::moveToUci(m);
      }
    } else
      fen_plus_moves += " " + uci::moveToUci(m);
  }

  void endPgn() {
    fens.push_back(fen_plus_moves);
    board.setFen(constants::STARTPOS);
    still_in_cdb = true;
    fen_plus_moves = constants::STARTPOS;
  }

private:
  std::uintptr_t handle;
  Board board;
  Movelist moves;
  bool still_in_cdb = true;
  std::string fen_plus_moves = constants::STARTPOS;
};

int main(int, char const *argv[]) {
  const auto file = argv[1];
  auto file_stream = std::ifstream(file);

  std::uintptr_t handle = cdbdirect_initialize(CHESSDB_PATH);
  std::uint64_t size = cdbdirect_size(handle);
  std::cout << "Opened DB with " << size << " stored positions." << std::endl;

  auto vis = std::make_unique<MyVisitor>(handle);

  pgn::StreamParser parser(file_stream);
  auto error = parser.readGames(*vis);

  handle = cdbdirect_finalize(handle);

  if (error) {
    std::cerr << "Error: " << error.message() << "\n";
    return 1;
  }

  auto outfile = std::ofstream("litrack_dump.epd");
  for (auto &fen : fens)
    outfile << fen << std::endl;

  std::cout << "Stored exit ply info for " << fens.size()
            << " games in litrack_dump.epd." << std::endl;

  return 0;
}
