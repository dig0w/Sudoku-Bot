<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h2 align="center">Sudoku Bot</h2>

  <p align="center">
    Sudoku bot using AI for digit recognition and hybrid rule/brute-force solving.
    <br />
    Automatically reads and fills puzzles from screen captures.
  </p>

  ## [![About View Desktop][product-screenshot9]](https://silasrodrigues.vercel.app)
</div>

<!-- Index -->
<details>
  <summary>Index</summary>
  <ol>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#requirements">Requirements</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

<!-- GETTING STARTED -->
## Getting Started

### Requirements
- Python 3.8+
- Windows, macOS, or Linux
- A visible Sudoku board on screen (supports sudoku.com, websudoku, etc.)


### Installation

1. Install requirements:
  ```sh
  pip install -r requirements.txt
  ```

2. Run the bot:
  ```sh
  python main.py
  ```

3. Press 'S' whenever you want him to start solving


<p align="right">(<a href="#Sudoku-Bot">back to top</a>)</p>

<!-- ABOUT THE PROJECT -->
## About The Project

This bot takes a screenshot of your screen and detects the largest square, assumed to be the Sudoku board.
Once the board is located, it extracts all 81 cells (9x9) and uses a custom CNN to recognize the digits.
Using basic Sudoku rules (and brute-force when necessary), it solves the puzzle, then automatically fills in the answers by simulating mouse clicks and key presses.

On average, the bot can solve a Sudoku puzzle in ~13 seconds.

The CNN was trained from scratch on a custom dataset built from screenshots of multiple Sudoku games, allowing it to recognize digits across different fonts and styles.

<p align="right">(<a href="#Sudoku-Bot">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [x] CNN digit recognition
- [x] Rule-based + brute-force solver
- [x] Auto-input
- [x] Enhanced preprocessing for low-contrast boards

See the [open issues](https://github.com/dig0w/sudoku-bot/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#Sudoku-Bot">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

<p align="right">(<a href="#Sudoku-Bot">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#Sudoku-Bot">back to top</a>)</p>


**🔗 Project Link:** [github.com/dig0w/sudoku-bot](https://github.com/dig0w/sudoku-bot)

[product-screenshot9]: ./preview.gif
