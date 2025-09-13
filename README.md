## Getting Started

You will need to install the requirements by running the following command:

```bash
pip install -r requirements.txt
```

Set your `MOODLE_TOKEN` and `MOODLE_URL`:

```bash
export MOODLE_URL="https://moodle.domain.xyz"
export MOODLE_TOKEN="1234567889"
```

[How to find your Moodle Token?](docs/token.md)

or you could provide these via arguments:
```bash
python moodlemagnet.py --token '1234567889' --url 'https://moodle.domain.xyz'
```

To run MoodleMagnet:
```bash
python moodlemagnet.py
```

Per default all files will be downloaded to the current directory. 
For more parameters look here:
```
Usage: moodlemagnet.py [OPTIONS]

  CLI tool to scrape data from Moodle courses.

  Provide --token and --url argument and start the dumping your moodle files.

Options:
  --token TEXT      Insert your token from the LMS Settings Security-Key Page.
  --cid TEXT        The ID of the course to scrape data from.
  --save_path TEXT  Path to save the data. Defaults to current directory.
  --url TEXT        Insert URL for LMS endpoint.
  --help            Show this message and exit.
```

## Testing

To run the basic functionality tests:
```bash
python test_examples.py --basic
```

To run the comprehensive test suite:
```bash
python test_examples.py
```

For pytest (after installing with `pip install pytest`):
```bash
pytest test_examples.py -v
```

## Recent Improvements

This codebase has been enhanced with several quality and security improvements:

- **Fixed Syntax Issues**: Resolved regex warnings and typos
- **Enhanced Security**: Token authentication uses headers instead of URL parameters
- **Better Code Organization**: Added helper functions and type hints
- **Improved Error Handling**: Better input validation and error messages
- **Added Testing**: Basic test suite to validate functionality

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for detailed improvement recommendations and implementation roadmap.




