#include <chrono>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include "../cdbdirect/cdbdirect.h"
#include "external/chess.hpp"

using namespace chess;

std::vector<std::string> fens;

const int tb_limit = 7; // dumps do not contain 7men EGTB positions

bool is_pos_in_cdb(std::uintptr_t handle, const Board &board) {
  auto result = cdbdirect_get(handle, board.getFen(false));
  int ply = result.back().second;
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
      // do not probe/collect moves leading to (stale)mate or 7men EGTB
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

int main(int argc, char const *argv[]) {
  if (argc < 2 || argc > 3) {
    std::cerr << "Usage: " << argv[0] << " <pgn_file> [<out_file>]\n\n";
    std::cerr
        << "For a collection of games find their exit from a cdb dump "
           "and save the last\nknown position and the rest of the game "
           "in the format\n\n  <FEN> [moves <m1> <m2> ...]\n\nas long as the "
           "moves do not lead to TB7 or (stale)mate.\n";
    return 1;
  }

  const auto file = argv[1];
  auto file_stream = std::ifstream(file);
  if (!file_stream.is_open()) {
    std::cerr << "Error: Could not open file " << file << std::endl;
    return 1;
  }

  const auto outfile = argc == 3 ? argv[2] : "lichess_dump.epd";

  std::uintptr_t handle = cdbdirect_initialize(CHESSDB_PATH);
  std::uint64_t size = cdbdirect_size(handle);
  std::cout << "Opened DB with " << size << " stored positions." << std::endl;

  const auto t0 = std::chrono::high_resolution_clock::now();

  auto vis = std::make_unique<MyVisitor>(handle);

  pgn::StreamParser parser(file_stream);
  auto error = parser.readGames(*vis);

  handle = cdbdirect_finalize(handle);

  const auto t1 = std::chrono::high_resolution_clock::now();

  std::cout << "Parsed " << fens.size() << " games in "
            << std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0)
                       .count() /
                   1000.0
            << "s\n";

  if (error) {
    std::cerr << "Error: " << error.message() << "\n";
    return 1;
  }

  auto outfile_stream = std::ofstream(outfile);
  for (auto &fen : fens)
    outfile_stream << fen << std::endl;

  std::cout << "Stored the exit ply info in " << outfile << "." << std::endl;

  return 0;
}
