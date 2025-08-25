# Steam Workshop Downloader

A Python GUI application for downloading Steam Workshop items using SteamCMD with automatic dependency resolution and batch download capabilities.

**_Always respect content creators' rights and Steam's Terms of Service_**.

## Motive

Created initially as a way to (re)learn python and to help me fulfill a need of mine of enjoyment :)

## Features

- **Simple GUI Interface**: Easy-to-use tkinter-based interface
- **Automatic Dependency Resolution**: Automatically detects and includes required dependencies
- **Batch Downloads**: Download multiple mods simultaneously
- **Progress Monitoring**: Real-time download progress with detailed logs
- **BBCode Description Support**: View formatted mod descriptions with BBCode parsing
- **Filtering and Search**: Filter mods by type (main mods/dependencies) and search by name/ID
- **Steam API Integration**: Fetches mod information directly from Steam
- **Error Handling**: Comprehensive error reporting and handling
- **Download Resume**: Handles interruptions gracefully

## Requirements

### System Requirements

- Windows, macOS, or Linux
- Python 3.7 or higher
- SteamCMD installed and accessible

### Python Dependencies

```
requests>=2.0.0
beautifulsoup4>=4.13.0
lxml>=4.6.0  # Optional: For faster HTML parsing
tkinterweb>=3.15.0  # Optional: For HTML rendering in descriptions
```

## Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/FallegaHQ/SteamWorkshopDownloader
   cd steam-workshop-downloader
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install SteamCMD**
    - Download SteamCMD from [Valve's website](https://developer.valvesoftware.com/wiki/SteamCMD)
    - Extract to a folder (e.g., `steamcmd/` in the project directory)

4. **Configure the application**
    - Edit `config.py` to set the correct path to your SteamCMD installation and other simple settings

## Usage

### Basic Usage

1. **Run the application**
   ```bash
   python main.py
   ```

2. **Add mods**
    - Paste a Steam Workshop URL into the input field
    - Click "Add Mod" or press Enter
    - The application will automatically fetch mod information and dependencies

3. **Download mods**
    - Select mods from the list (use Ctrl+Click for multiple selection)
    - Click "Download Selected" to download chosen mods and their dependencies
    - Or click "Download All" to download everything in the list

### Supported URL Formats

- `https://steamcommunity.com/sharedfiles/filedetails/?id=123456789`
- `https://steamcommunity.com/workshop/filedetails/?id=123456789`

### Features Overview

#### Filtering and Search

- Use the filter box to search by mod title, ID, or URL
- Toggle checkboxes to show/hide main mods and dependencies
- Clear filters with the "Clear" button

#### Dependency Management

- Dependencies are automatically detected and added
- Hierarchical view shows dependency relationships (with slight limitations)
- Dependencies are marked with special indicators in the list

#### Download Progress

- Real-time progress bar and status updates
- Detailed log window shows SteamCMD output
- Download completion summary with error reporting

#### Mod Information

- Click on any mod to view detailed information
- View formatted descriptions in a popup window
- Copy mod information to clipboard

## Configuration

Edit `config.py` to customize:

```python
# SteamCMD path
STEAMCMD_PATH = r"path/to/your/steamcmd.exe"

# Window dimensions
MAIN_WINDOW_WIDTH = 700
MAIN_WINDOW_HEIGHT = 650

# API settings
REQUEST_TIMEOUT = 10
```

## File Structure

```
steam-workshop-downloader/
├── main.py                          # Main application entry point
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── mod_manager.py                   # Mod data management
├── steamcmd_downloader.py           # SteamCMD interface
├── steam_api.py                     # Steam API communication
├── bbcode_parser.py                 # BBCode to HTML conversion - Specific to what BBCode found in SteamWorkshop descriptions - Please let me know if there's a better implementation
├── ui_components.py                 # UI widgets and helpers
├── download_completion_dialog.py    # Download results dialog
└── mods.json                        # Mod data storage (auto-generated)
```

## Data Storage

- Mod information is stored in `mods.json`
- This file is automatically created and updated
- Contains mod metadata, dependencies, and download status
- Safe to delete if you want to start fresh

## Troubleshooting

### Common Issues

**"SteamCMD not found"**

- Verify SteamCMD is installed and the path in `config.py` is correct
- Make sure you have execute permissions on the SteamCMD binary

**"No App ID found"**

- Some mods may not have valid App IDs
- This usually means the mod is no longer available or private

**Network timeouts**

- Check your internet connection
- Some Steam Workshop pages may be temporarily unavailable
- Increase `REQUEST_TIMEOUT` in `config.py` if needed

**Dependencies not showing**

- Dependencies are scraped from Workshop pages
- Some mods may not list dependencies properly
- Manual dependency resolution may be needed

### Performance Tips

1. **Install optional dependencies for better performance:**
   ```bash
   pip install -r requirements.txt
   ```

2. **For large mod lists:**
    - Use filtering to manage visibility
    - Download in smaller batches if experiencing issues
    - When filtered, mods will still download their dependencies alongside

3. **Network optimization:**
    - Close other applications using bandwidth during downloads
    - Consider downloading during off-peak hours

## Advanced Features

### Batch Operations

- Select multiple mods with Ctrl+Click or Shift+Click
- Bulk operations preserve dependency relationships
- Smart dependency resolution prevents duplicates

### Filtering Options

- Search by mod name, ID, or URL
- Show/hide main mods and dependencies separately
- Real-time filter application

### Description Viewing

- BBCode parsing for rich text formatting
- Fallback to plain text if tkinterweb is not available
- Open descriptions in external browser

## Development

### Adding New Features

The codebase is modular and well-documented:

- `ModManager`: Handles mod data and persistence
- `SteamCMDDownloader`: Manages SteamCMD operations
- `SteamAPI`: Interfaces with Steam's web API
- `BBCodeParser`: Converts BBCode to HTML
- UI components are separated into their own modules

### Contributing

As my time is limited, I will not be updating this tool, actively at least. If you have ideas, suggest them and I will try to provide updates to my best ability :)

If you can update the codebase, that would be **very appreciated ♥️**

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate documentation
4. Submit a pull request

## License

This project is provided as-is for educational and personal use. Please respect Steam's Terms of Service and only download content you have the right to access.

Commercial use is **Strictly Prohibited**!

**_Always respect content creators' rights and Steam's Terms of Service_**.

## Disclaimer

This tool is not affiliated with Valve Corporation or Steam. Use at your own risk and ensure you comply with Steam's Terms of Service and any applicable laws in your jurisdiction.

**_Always respect content creators' rights and Steam's Terms of Service_**.

## Support

For issues, feature requests, or questions:

1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information about your problem

---

**Note**: This application requires SteamCMD and is intended for legitimate use only.

**_Always respect content creators' rights and Steam's Terms of Service_**.