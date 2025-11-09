import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import re
import click
import datastructures as ds
import validators
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
DEFAULT_FILE_EXTENSIONS = [
    '.pdf', '.PDF', '.py', '.csv', '.xls', '.doc', '.docx', '.docm', '.ipynb',
    '.jpg', '.jpeg', '.png', '.md', '.html', '.ppt', '.pptx', '.txt', '.tex'
]

BANNER = """
███╗   ███╗ ██████╗  ██████╗ ██████╗ ██╗     ███████╗    ███╗   ███╗ █████╗  ██████╗ ███╗   ██╗███████╗████████╗
████╗ ████║██╔═══██╗██╔═══██╗██╔══██╗██║     ██╔════╝    ████╗ ████║██╔══██╗██╔════╝ ████╗  ██║██╔════╝╚══██╔══╝
██╔████╔██║██║   ██║██║   ██║██║  ██║██║     █████╗      ██╔████╔██║███████║██║  ███╗██╔██╗ ██║█████╗     ██║   
██║╚██╔╝██║██║   ██║██║   ██║██║  ██║██║     ██╔══╝      ██║╚██╔╝██║██╔══██║██║   ██║██║╚██╗██║██╔══╝     ██║   
██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██████╔╝███████╗███████╗    ██║ ╚═╝ ██║██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   
╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝                                                                                                                   
"""

def clean_filename(url: str) -> str:
    """
    Clean the filename extracted from the URL to remove tokens and unwanted characters.
    """

    filename = url.split('/')[-1]
    
    filename = re.split(r'\?|&', filename)[0]

    # Remove reserved characters for Windows
    filename = re.sub(r'[<>:"/\|?*]', '', filename)
    
    return filename

# Cache annotation keys for better performance
_SECTION_KEYS = None
_COMPLETION_DATA_KEYS = None
_MODULE_KEYS = None
_CONTENT_KEYS = None
_RECENT_COURSE_KEYS = None

def _get_section_keys():
    global _SECTION_KEYS
    if _SECTION_KEYS is None:
        _SECTION_KEYS = set(ds.Section.__annotations__.keys())
    return _SECTION_KEYS

def _get_completion_data_keys():
    global _COMPLETION_DATA_KEYS
    if _COMPLETION_DATA_KEYS is None:
        _COMPLETION_DATA_KEYS = set(ds.CompletionData.__annotations__.keys())
    return _COMPLETION_DATA_KEYS

def _get_module_keys():
    global _MODULE_KEYS
    if _MODULE_KEYS is None:
        _MODULE_KEYS = set(ds.Module.__annotations__.keys())
    return _MODULE_KEYS

def _get_content_keys():
    global _CONTENT_KEYS
    if _CONTENT_KEYS is None:
        _CONTENT_KEYS = set(ds.Content.__annotations__.keys())
    return _CONTENT_KEYS

def _get_recent_course_keys():
    global _RECENT_COURSE_KEYS
    if _RECENT_COURSE_KEYS is None:
        _RECENT_COURSE_KEYS = set(ds.RecentCourse.__annotations__.keys())
    return _RECENT_COURSE_KEYS

def deserialize_section(section_data: dict) -> ds.Section:
    modules = [deserialize_module(
        module_data) for module_data in section_data.get('modules', [])]

    # Extract only the fields that match the Section dataclass attributes
    keys = _get_section_keys()
    relevant_data = {
        key: section_data[key] for key in keys if key in section_data}
    relevant_data['modules'] = modules

    return ds.Section(**relevant_data)

def deserialize_completion_data(completion_data_dict: dict) -> ds.CompletionData:
    # Extract only the fields that match the CompletionData dataclass attributes
    keys = _get_completion_data_keys()
    relevant_data = {
        key: completion_data_dict[key] for key in keys if key in completion_data_dict}
    return ds.CompletionData(**relevant_data)

def deserialize_module(module_data: dict) -> ds.Module:
    keys = _get_module_keys()
    relevant_data = {
        key: module_data[key] for key in keys if key in module_data}

    if 'completiondata' in module_data:
        relevant_data['completiondata'] = deserialize_completion_data(
            module_data['completiondata'])

    return ds.Module(**relevant_data)


def deserialize_content(content_data: dict) -> ds.Content:
    keys = _get_content_keys()
    relevant_data = {key: content_data[key] for key in keys if key in content_data}
    return ds.Content(**relevant_data)

def deserialize_recent_course(course_data: dict) -> ds.RecentCourse:
    keys = _get_recent_course_keys()
    relevant_data = {key: course_data[key] for key in keys if key in course_data}
    return ds.RecentCourse(**relevant_data)


def unpack_contents(sections: List[ds.Section]) -> List[str]:
    """Unpack contents from sections and return list of filenames.
    
    Optimized to do deserialization and collection in a single pass.
    """
    filenames = []
    
    for section in sections:
        for module in section.modules:
            if isinstance(module.contents, list):
                # Deserialize contents and collect filenames in one pass
                deserialized_contents = []
                for content_data in module.contents:
                    if isinstance(content_data, dict):
                        content = deserialize_content(content_data)
                        deserialized_contents.append(content)
                        filenames.append(content.filename)
                    else:
                        deserialized_contents.append(content_data)
                        filenames.append(content_data.filename)
                module.contents = deserialized_contents
            elif module.contents:
                # Already deserialized, just collect filenames
                for content in module.contents:
                    filenames.append(content.filename)

    return filenames


def validate_inputs(url: str, token: str) -> Optional[str]:
    """Validate URL and token inputs. Returns error message if invalid, None if valid."""
    if not url:
        return "Please set a URL endpoint, either with a environment variable or via the --url argument."
    if not token:
        return "Please set a MOODLE_TOKEN, either with a environment variable or via the --token argument."
    if not validators.url(url):
        return "Not a valid URL. Please check your MOODLE_URL."
    return None


def build_moodle_url(base_url: str, endpoint: str, **params: str) -> str:
    """Build a properly formatted Moodle API URL without token in URL."""
    url = f"{base_url}/moodle/webservice/rest/server.php?wsfunction={endpoint}&moodlewsrestformat=json"
    for key, value in params.items():
        if value is not None:
            url += f"&{key}={value}"
    return url


def make_moodle_request(url: str, token: str) -> requests.Response:
    """Make a request to Moodle API with token in headers for security."""
    # Note: Some Moodle installations may require token in URL for web services
    # This is a more secure approach but may need fallback to URL-based token
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'MoodleMagnet/1.0'
    }
    
    # Try with Authorization header first, fallback to URL parameter if needed
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 401:  # If unauthorized, try with token in URL
            url_with_token = f"{url}&wstoken={token}" if '?' in url else f"{url}?wstoken={token}"
            response = requests.get(url_with_token)
        return response
    except requests.RequestException:
        # Fallback to URL-based token
        url_with_token = f"{url}&wstoken={token}" if '?' in url else f"{url}?wstoken={token}"
        return requests.get(url_with_token)


def create_download_session() -> requests.Session:
    """Create a requests session with connection pooling and retry logic."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # Mount adapter with connection pooling
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def download_file(url: str, folder: str, session: Optional[requests.Session] = None) -> Tuple[bool, str]:
    """Download a single file with error handling.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if session is None:
        session = requests
        
    try:
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()

        filename = os.path.join(folder, clean_filename(url))
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, filename
                
    except requests.RequestException as e:
        return False, f"Error downloading {url}: {e}"
    except IOError as e:
        return False, f"Error saving file: {e}"


def download_files_parallel(file_urls: List[Tuple[str, str]], max_workers: int = 5) -> List[Tuple[bool, str]]:
    """Download multiple files in parallel using a thread pool.
    
    Args:
        file_urls: List of (url, folder) tuples
        max_workers: Maximum number of concurrent downloads
        
    Returns:
        List of (success, message) tuples for each download
    """
    session = create_download_session()
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_url = {
            executor.submit(download_file, url, folder, session): (url, folder)
            for url, folder in file_urls
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                url, _ = future_to_url[future]
                results.append((False, f"Unexpected error for {url}: {e}"))
    
    return results



@click.command()
@click.option('--token', default=lambda: os.environ.get("MOODLE_TOKEN", ""), help='Insert your token from the LMS Settings Security-Key Page.')
@click.option('--cid', required=False, help='The ID of the course to scrape data from.')
@click.option('--save_path', default=os.getcwd(), help='Path to save the data. Defaults to current directory.')
@click.option(
    "--url",
    default=lambda: os.environ.get("MOODLE_URL", ""),
    help='Insert URL for LMS endpoint.'
)
def scrape_data(cid: Optional[str], save_path: str, token: str, url: str) -> None:
    """
    CLI tool to scrape data from Moodle courses.

    Provide --token and --url argument and start the dumping your moodle files.
    """
    # Display banner
    click.echo(click.style(BANNER, fg='green'))
    
    # Validate inputs
    error_msg = validate_inputs(url, token)
    if error_msg:
        return click.secho(error_msg, fg='red')

    
    try:
        # Build API URLs using helper function
        recent_courses_url = build_moodle_url(url, "core_course_get_recent_courses")
        assignments_content_url = build_moodle_url(url, "mod_assign_get_assignments", **{"courseids[]": cid} if cid else {})
        
        
        response_recent_courses = make_moodle_request(recent_courses_url, token)

        # Check if token is valid
        if b"invalidtoken" in response_recent_courses.content:
            return click.secho("Your provided Token seems invalid. Please check your MOODLE_TOKEN.",
                                fg='red')

        response_recent_courses.raise_for_status()



        response_assignments = make_moodle_request(assignments_content_url, token)
        response_assignments.raise_for_status()

        recent_course_contents = response_recent_courses.json()
        recent_courses = [deserialize_recent_course(course_data) for course_data in recent_course_contents]

        course_content_folder = os.path.join(save_path, "Course_Content")
        assignments_folder = os.path.join(save_path, "Assignments")
        os.makedirs(course_content_folder, exist_ok=True)
        os.makedirs(assignments_folder, exist_ok=True)
    


        def display_courses(recent_courses: List[ds.RecentCourse], cid: Optional[str]) -> str:
            if not cid:
                click.echo("")
                click.echo("You are in the following courses:")
                click.echo("")
                click.echo(click.style("ID   |  NAME", fg='blue'))
                tmp_ids = []
                for y in recent_courses:
                    if y.hidden: # Only show your active courses
                        pass
                    else:
                        click.echo(f"{(y.id)} {(y.fullname)}")
                        tmp_ids.append(y.id)
                    
                click.echo("")
                
                value = click.prompt('Which course do you want to dump? [COURSE ID] ', type=int)
            else:
                return build_moodle_url(url, "core_course_get_contents", courseid=cid)
        
            if value and value in tmp_ids:
                cid = value
                return build_moodle_url(url, "core_course_get_contents", courseid=str(cid))
            else:
                click.echo('Invalid input :(. Please try again')

        content_url = display_courses(recent_courses, cid)


        
        response = make_moodle_request(content_url, token)   
 
        response.raise_for_status()
       
        course_contents = response.json()



        # Deserializing the JSON data again using the adjusted functions
        sections = [deserialize_section(section_data) for section_data in course_contents]



        if not course_contents or "exception" in course_contents:
            click.echo(f"Invalid course ID or no content found for course {cid}.")
            return

    except requests.RequestException as e:
        click.echo(f"Error retrieving course content: {e}")
        return


    ##### PRINT CONSOLE
    click.echo("Received the following content:")
    click.echo("")
    for x in unpack_contents(sections):
         click.echo(click.style(x, fg='white'))
    
    click.echo("")
    click.echo(click.style("Do you want to download these files now?", fg='blue'))
    click.echo('Continue? [y/n] ', nl=False)
    c = click.getchar()
    click.echo()
    if c == 'y':
        click.echo('Starting download...')
    elif c == 'n':
        click.echo('Abort!')
        return
    else:
        click.echo('Invalid input :(')
        return

    ####### DOWNLOAD PART
    # Pre-compile extension check set for faster lookup
    extension_set = set(DEFAULT_FILE_EXTENSIONS)
    
    # Use deserialized sections instead of raw JSON data
    file_urls: List[Tuple[str, str]] = []
    for section in sections:
        for module in section.modules:
            if module.contents:
                for content in module.contents:
                    # Check if file extension matches using set lookup (O(1) vs O(n))
                    if any(content.filename.endswith(ext) for ext in extension_set):
                        file_urls.append((content.fileurl + f"?&token={token}", course_content_folder))

    if not file_urls:
        click.echo("No Files found in the specified course.")
        return

    # Use parallel downloads for better performance
    click.echo(f"Downloading {len(file_urls)} files...")
    results = download_files_parallel(file_urls, max_workers=5)
    
    # Report results
    successful = sum(1 for success, _ in results if success)
    failed = len(results) - successful
    
    click.echo(f"✓ Successfully downloaded {successful} files to {save_path}")
    if failed > 0:
        click.echo(f"✗ Failed to download {failed} files")
        # Show first few errors
        errors = [msg for success, msg in results if not success]
        for error in errors[:3]:
            click.echo(f"  - {error}")
        if len(errors) > 3:
            click.echo(f"  ... and {len(errors) - 3} more errors")

if __name__ == '__main__':
    scrape_data()