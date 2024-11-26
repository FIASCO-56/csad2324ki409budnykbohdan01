#include <Arduino.h>

char board[3][3];
bool gameActive = false;
String player1Symbol = "X";
String player2Symbol = "O";
String currentPlayer = "X";
int gameMode = 0;

struct GameConfig {
  int gameMode;
  String player1Symbol;
  String player2Symbol;
  String currentPlayer;
};


void saveConfig(const GameConfig &config) {
    String output;
    output += "<GameConfig> ";

    output += "  <GameMode>" + String(config.gameMode) + "</GameMode> ";
    output += "  <Player1Symbol>" + config.player1Symbol + "</Player1Symbol> ";
    output += "  <Player2Symbol>" + config.player2Symbol + "</Player2Symbol> ";

    output += "</GameConfig>";

    Serial.println(output);
}


bool loadStringConfig(const String& xml, const char* key, String& value) {
    String startTag = "<" + String(key) + ">";
    String endTag = "</" + String(key) + ">";

    int startIndex = xml.indexOf(startTag);
    int endIndex = xml.indexOf(endTag);

    if (startIndex != -1 && endIndex != -1) {
        startIndex += startTag.length();
        value = xml.substring(startIndex, endIndex);
        value.trim();
        return true;
    }

    Serial.println(String(key) + " not found or invalid");
    return false;
}

void loadConfig(String xmlConfig) {
    String gameModeTag = "<GameMode>";
    String gameModeEndTag = "</GameMode>";

    int startIndex = xmlConfig.indexOf(gameModeTag);
    int endIndex = xmlConfig.indexOf(gameModeEndTag);

    if (startIndex != -1 && endIndex != -1) {
        startIndex += gameModeTag.length();
        String gameModeStr = xmlConfig.substring(startIndex, endIndex);
        gameModeStr.trim();
        gameMode = gameModeStr.toInt();
    } else {
        Serial.println("gameMode not found");
        return;
    }

    if (!loadStringConfig(xmlConfig, "Player1Symbol", player1Symbol)) return;
    if (!loadStringConfig(xmlConfig, "Player2Symbol", player2Symbol)) return;

    Serial.println("Configuration loaded!");
}


void initializeBoard() {
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      board[i][j] = ' ';
    }
  }
}

void printBoard() {
  String boardState = "Board state:\n";
  
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      if (board[i][j] == 'X' || board[i][j] == 'O') {
        boardState += board[i][j]; 
      } else {
        boardState += '.';
      }
      if (j < 2) boardState += "|"; 
    }
    if (i < 2) boardState += "\n-+-+-\n"; 
    else boardState += "\n"; 
  }

  Serial.println(boardState);
}

bool checkWin(char player) {
  for (int i = 0; i < 3; i++) {
    if ((board[i][0] == player && board[i][1] == player && board[i][2] == player) || 
        (board[0][i] == player && board[1][i] == player && board[2][i] == player)) { 
      return true;
    }
  }
  
  if ((board[0][0] == player && board[1][1] == player && board[2][2] == player) ||
      (board[0][2] == player && board[1][1] == player && board[2][0] == player)) {
    return true;
  }
  
  return false;
}

bool isBoardFull() {
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      if (board[i][j] == ' ') {
        return false;
      }
    }
  }
  return true; 
}

void aiMove(char aiSymbol) {
  if (blockOpponentMove(aiSymbol == 'X' ? 'O' : 'X')) {
    return; 
  }

  int startX = random(3); 
  int startY = random(3);

  if (random(2) == 0) {
    startX = 0; 
    startY = 0;
  }

  for (int i = startX; i < 3; i++) {
    for (int j = startY; j < 3; j++) {
      if (board[i][j] == ' ') {
        board[i][j] = aiSymbol;
        Serial.println("AI played at: " + String(i + 1) + " " + String(j + 1));
        return;
      }
    }
  }

  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      if (board[i][j] == ' ') {
        board[i][j] = aiSymbol;
        Serial.println("AI played randomly at: " + String(i + 1) + " " + String(j + 1));
        return;
      }
    }
  }
}

bool blockOpponentMove(char opponent) {
  int row[3] = {0, 1, 2};
  int col[3] = {0, 1, 2};

  // Check rows and columns
  for (int i = 0; i < 3; i++) {
    int rowCoords[3][2] = {{row[i], 0}, {row[i], 1}, {row[i], 2}};
    int colCoords[3][2] = {{0, col[i]}, {1, col[i]}, {2, col[i]}};

    if (canBlock(rowCoords[0], rowCoords[1], rowCoords[2], opponent)) {
      return true;
    }
    if (canBlock(colCoords[0], colCoords[1], colCoords[2], opponent)) {
      return true;
    }
  }

  // Check diagonals
  int diag1[3][2] = {{0, 0}, {1, 1}, {2, 2}};
  int diag2[3][2] = {{0, 2}, {1, 1}, {2, 0}};

  if (canBlock(diag1[0], diag1[1], diag1[2], opponent)) {
    return true;
  }
  if (canBlock(diag2[0], diag2[1], diag2[2], opponent)) {
    return true;
  }

  return false;
}

bool isWinningMove(int coords1[2], int coords2[2], int coords3[2], char opponent) {
  return (board[coords1[0]][coords1[1]] == opponent && board[coords2[0]][coords2[1]] == opponent && board[coords3[0]][coords3[1]] == ' ') ||
         (board[coords1[0]][coords1[1]] == opponent && board[coords2[0]][coords2[1]] == ' ' && board[coords3[0]][coords3[1]] == opponent) ||
         (board[coords1[0]][coords1[1]] == ' ' && board[coords2[0]][coords2[1]] == opponent && board[coords3[0]][coords3[1]] == opponent);
}

void placeMove(int coords[2], char symbol) {
  board[coords[0]][coords[1]] = symbol;
  Serial.println("AI blocked opponent's winning move at: " + String(coords[0] + 1) + " " + String(coords[1] + 1));
}

bool canBlock(int coords1[2], int coords2[2], int coords3[2], char opponent) {
  if (isWinningMove(coords1, coords2, coords3, opponent)) {
    if (board[coords1[0]][coords1[1]] == ' ') {
      placeMove(coords1, 'O');
    } else if (board[coords2[0]][coords2[1]] == ' ') {
      placeMove(coords2, 'O');
    } else {
      placeMove(coords3, 'O');
    }
    return true;
  }

  return false;
}

void handlePlayerMove(int row, int col) {
  board[row][col] = (currentPlayer == "X") ? 'X' : 'O';
  printBoard();

  if (checkWin('X')) {
    Serial.println("Player X wins!");
    gameActive = false;
  } else if (checkWin('O')) {
    Serial.println("Player O wins!");
    gameActive = false;
  } else if (isBoardFull()) {
    Serial.println("It's a draw!");
    gameActive = false;
  }
}

void handleAIMove() {
  if (gameMode == 2) {
    aiMove(player1Symbol[0]);
    if (checkWin(player1Symbol[0])) {
      Serial.println("Player 1 (AI) wins!");
      gameActive = false;
      return;
    }
    aiMove(player2Symbol[0]);
    if (checkWin(player2Symbol[0])) {
      Serial.println("Player 2 (AI) wins!");
      gameActive = false;
      return;
    }
  }
}

void switchPlayer() {
  currentPlayer = (currentPlayer == "X") ? 'O' : 'X';
}

bool isValidMove(int row, int col) {
  return (row >= 0 && row < 3 && col >= 0 && col < 3 && board[row][col] == ' ');
}

void processMove(String input) {
  int row = input[0] - '1';
  int col = input[2] - '1';

  if (isValidMove(row, col)) {
    handlePlayerMove(row, col);
    
    if (!gameActive) return;

    handleAIMove();

    if (gameActive) {
      switchPlayer();
    }
  } else {
    Serial.println("Invalid move, try again.");
  }
}


void setup() {
  Serial.begin(9600);
}

void initializeGame() {
  initializeBoard();
  gameActive = true;

  if (gameMode == 1) {
    Serial.println("Player 1, choose your symbol: X or O");
    currentPlayer = (random(2) == 0) ? 'X' : 'O';
    player1Symbol = currentPlayer;
    player2Symbol = (currentPlayer == "X") ? 'O' : 'X';
    Serial.println("Player 1 is " + String(player1Symbol));
    Serial.println("Player 2 is " + String(player2Symbol));
  } else {
    currentPlayer = 'X';
  }

  Serial.println("New game started! " + String(currentPlayer) + " goes first.");
  printBoard();
}

bool checkAndPrintWinner(char symbol) {
  if (checkWin(symbol)) {
    Serial.println(String(symbol) + " wins!");
    gameActive = false;
    return true;
  }
  return false;
}

bool checkAndPrintDraw() {
  if (isBoardFull()) {
    Serial.println("It's a draw!");
    gameActive = false;
    return true;
  }
  return false;
}

void processHumanVsAI() {
  while (gameActive) {
    if (currentPlayer == "X") {
      Serial.println("Your move, player (enter row and column):");
      while (Serial.available() == 0) {}
      String userMove = Serial.readStringUntil('\n');
      processMove(userMove);
      printBoard();

      if (checkAndPrintWinner('X') || checkAndPrintDraw()) {
        break;
      }

      currentPlayer = 'O';
    } else {
      aiMove('O');
      printBoard();
      if (checkAndPrintWinner('O') || checkAndPrintDraw()) {
        break;
      }

      currentPlayer = 'X';
    }
  }
}

void processAIvsAI() {
  while (gameActive) {
    aiMove('X');
    printBoard();
    if (checkAndPrintWinner('X') || checkAndPrintDraw()) {
      break;
    }

    aiMove('O');
    printBoard();
    if (checkAndPrintWinner('O') || checkAndPrintDraw()) {
      break;
    }
  }
}

void processReceivedMessage(String receivedMessage) {
  if (receivedMessage == "new") {
    initializeGame();
    
    if (gameMode == 0) {
      processHumanVsAI();
    } else if (gameMode == 2) {
      processAIvsAI();
    }
  } else if (receivedMessage.startsWith("save")) {
    GameConfig config = { gameMode, player1Symbol, player2Symbol, currentPlayer };
    saveConfig(config);
  } else if (receivedMessage.startsWith("<")) {
    if (receivedMessage.length() > 0) {
        loadConfig(receivedMessage);
    } else {
        Serial.println("No message received");
    }
  } else if (receivedMessage.startsWith("modes")) {
    handleGameMode(receivedMessage);
  } else if (gameActive) {
    processMove(receivedMessage);
  } else {
    Serial.println("No active game. Type 'new' to start.");
  }
}

void handleGameMode(String receivedMessage) {
  if (receivedMessage == "modes 0") {
    gameMode = 0;
    Serial.println("Game mode: Man vs AI");
  } else if (receivedMessage == "modes 1") {
    gameMode = 1;
    Serial.println("Game mode: Man vs Man");
  } else if (receivedMessage == "modes 2") {
    gameMode = 2;
    Serial.println("Game mode: AI vs AI");
  }
}

void loop() {
  if (Serial.available() > 0) {
    String receivedMessage = Serial.readStringUntil('\n');
    receivedMessage.trim();
    processReceivedMessage(receivedMessage);
  }
}
