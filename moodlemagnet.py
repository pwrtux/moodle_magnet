import requests
import os
import re
import click
import datastructures as ds

def clean_filename(url):
    """
    Clean the filename extracted from the URL to remove tokens and unwanted characters.
    """

    filename = url.split('/')[-1]
    
    filename = re.split('\?|&', filename)[0]

    # Remove reserved characters for Windows
    filename = re.sub(r'[<>:"/\|?*]', '', filename)
    
    return filename

def deserialize_section(section_data: dict) -> ds.Section:
    modules = [deserialize_module(
        module_data) for module_data in section_data.get('modules', [])]

    # Extract only the fields that match the Section dataclass attributes
    relevant_data = {
        key: section_data[key] for key in ds.Section.__annotations__ if key in section_data}
    relevant_data['modules'] = modules

    return ds.Section(**relevant_data)

def deserialize_completion_data(completion_data_dict: dict) -> ds.CompletionData:
    # Extract only the fields that match the CompletionData dataclass attributes
    relevant_data = {
        key: completion_data_dict[key] for key in ds.CompletionData.__annotations__ if key in completion_data_dict}
    return ds.CompletionData(**relevant_data)

def deserialize_module(module_data: dict) -> ds.Module:
    relevant_data = {
        key: module_data[key] for key in ds.Module.__annotations__ if key in module_data}

    if 'completiondata' in module_data:
        relevant_data['completiondata'] = deserialize_completion_data(
            module_data['completiondata'])

    return ds.Module(**relevant_data)


def deserialize_content(content_data: dict) -> ds.Content:
    relevant_data = {key: content_data[key] for key in ds.Content.__annotations__ if key in content_data}
    return ds.Content(**relevant_data)

def deserialize_recent_course(course_data: dict) -> ds.RecentCourse:
    relevant_data = {key: course_data[key] for key in ds.RecentCourse.__annotations__ if key in course_data}
    return ds.RecentCourse(**relevant_data)


def unpack_contents(sections):
    for section in sections:
        for module in section.modules:
            if isinstance(module.contents, list):
                module.contents = [deserialize_content(content_data) if isinstance(content_data, dict) else content_data for content_data in module.contents]

    filenames = []

    for section in sections:
        for module in section.modules:
            if module.contents: 
                for content in module.contents:
                    filenames.append(content.filename)

    return filenames



BANNER =  """
███╗   ███╗ ██████╗  ██████╗ ██████╗ ██╗     ███████╗    ███╗   ███╗ █████╗  ██████╗ ███╗   ██╗███████╗████████╗
████╗ ████║██╔═══██╗██╔═══██╗██╔══██╗██║     ██╔════╝    ████╗ ████║██╔══██╗██╔════╝ ████╗  ██║██╔════╝╚══██╔══╝
██╔████╔██║██║   ██║██║   ██║██║  ██║██║     █████╗      ██╔████╔██║███████║██║  ███╗██╔██╗ ██║█████╗     ██║   
██║╚██╔╝██║██║   ██║██║   ██║██║  ██║██║     ██╔══╝      ██║╚██╔╝██║██╔══██║██║   ██║██║╚██╗██║██╔══╝     ██║   
██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██████╔╝███████╗███████╗    ██║ ╚═╝ ██║██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   
╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝                                                                                                                   
"""


click.echo(click.style(BANNER, fg='green'))
@click.command()
@click.option('--token', required=True, help='Insert your token from the LMS Settings Security-Key Page.')
@click.option('--cid', required=False, help='The ID of the course to scrape PDFs from.')
@click.option('--save_path', default=os.getcwd(), help='Path to save the PDFs. Defaults to current directory.')
@click.option(
    "--url",
    default=lambda: os.environ.get("MOODLE_URL", "")
)
def scrape_pdfs(cid, save_path, token, url):
    """
    CLI tool to scrape data from Moodle courses.

    Provide --token and --url argument and start the dumping your moodle files.
    """
    

    if url == "":
        return click.echo("Please set a URL endpoint, either with a environment variable or via the --url parameter.")

    file_extensions = ['.pdf', '.PDF' , '.py', '.csv', '.xls', '.doc', '.ipynb', '.jpg', '.jpeg', '.png', '.md', '.html']

    course_content_folder = os.path.join(save_path, "Course_Content")
    assignments_folder = os.path.join(save_path, "Assignments")
    os.makedirs(course_content_folder, exist_ok=True)
    os.makedirs(assignments_folder, exist_ok=True)

    try:
    

        recent_courses_url = f"{url}?wstoken={token}&wsfunction=core_course_get_recent_courses&moodlewsrestformat=json"
        respose_recent_courses_response = requests.get(recent_courses_url)
        respose_recent_courses_response.raise_for_status()


        assignments_content_url = f"{url}?wstoken={token}&wsfunction=mod_assign_get_assignments&courseids[]={cid}&moodlewsrestformat=json"

        respose_assignments = requests.get(assignments_content_url)

        respose_assignments.raise_for_status()

        recent_course_contents = respose_recent_courses_response.json()
        recent_courses = [deserialize_recent_course(course_data) for course_data in recent_course_contents]


        def display_courses(recent_courses, cid) -> str:
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
                course_content_url = f"{url}?wstoken={token}&wsfunction=core_course_get_contents&courseid={cid}&moodlewsrestformat=json"
                return course_content_url
        
            if value and value in tmp_ids:
                cid = value
                course_content_url = f"{url}?wstoken={token}&wsfunction=core_course_get_contents&courseid={cid}&moodlewsrestformat=json"
                return course_content_url
            else:
                click.echo('Invalid input :(. Please try again')

        content_url = display_courses(recent_courses, cid)


        
        response = requests.get(content_url)   
 
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
    file_urls = []
    for section in course_contents:
        for module in section.get('modules', []):
            for content in module.get('contents', []):
                if any(content['filename'].endswith(ext) for ext in file_extensions):
                    file_urls.append((content['fileurl'] + f"?&token={token}", course_content_folder))

    if not file_urls:
        click.echo("No Files found in the specified course.")
        return

    with click.progressbar(file_urls, label='Downloading Files') as bar:
        for url,folder in bar:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()

                filename = os.path.join(folder, clean_filename(url))
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            except requests.RequestException as e:
                click.echo(f"Error downloading {url}: {e}")
            except IOError as e:
                click.echo(f"Error saving {filename}: {e}")

    click.echo(f"Downloaded Files to {save_path}")

if __name__ == '__main__':
    scrape_pdfs()