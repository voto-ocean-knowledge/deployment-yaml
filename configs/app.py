from pathlib import Path
import streamlit as st
from reader import run_checker_on_dir
st.set_page_config(page_title='Config Checker', page_icon = "🔥",)# layout = 'wide')
st.title("Config Checker for SeaExplorer")

runnable = False
fmt_colors = {
    'WARNING': 'orange',
    'ERROR': 'red',
}



dir_string = st.text_input(r'Input directory path ')
if "\\" in dir_string:
    dir_string = dir_string.replace("\\", "/")
    
if dir_string[:4] != "/mnt":
    if '1_Operations/' in dir_string:
        dir_base, dir_append = dir_string.split('1_Operations/')
        dir_string = "/mnt/docs/1_Operations/" + dir_append

dir_path = Path(dir_string)
if dir_path.is_file():
    dir_path = dir_path.parent

multi_line = r'''Please enter a directory which contains glider config files. Acceptable formats include:  
- `/mnt/docs/1_Operations/Missions/23_Phycoglider_2/SEA077_PLD094/SEA077_M44`  
- `\docs\1_Operations\Missions\07_SAMBA_05\02_SAMBA_05_002\SEA079_PLD096\20250710_M34`  
     '''

if dir_path == Path(""):
    st.markdown(multi_line)
elif dir_path.is_dir():
    runnable = True
    file_paths = dir_path.glob("*")
    files = [file_path.name for file_path in file_paths]
    st.write("The selected directory is ", dir_path)
    st.write("The directory contains ", files)
    essential_files =  {"sea.cfg", "sea.msn", "seapayload.cfg"}
    if list(dir_path.glob("seapayload*cfg")):
        essential_files.remove("seapayload.cfg")
        essential_files.add(list(dir_path.glob("seapayload*cfg"))[0].name)
    missing_files = essential_files.difference(files)
    if missing_files:
        st.write(f":red[Supplied directory is missing config files: {missing_files}]. The checker may not work!")
    else:
        st.write(f"Found all three config files needed by the checker {tuple(essential_files)} 👍")

    sea_files = list(dir_path.glob("SEA*")) + list(dir_path.glob("SHW*"))
    if sea_files:
        st.write(f"It looks like this is the directory of {sea_files[0].name.split('.')[0]}")
    if "config_check.log" in files:
        with open(dir_path / "config_check.log") as fin:
            for line in fin.readlines():
                if "START" in line:
                    last_check = line.split('check at ')[1][:20]
                    if last_check[:2] == "20":
                        st.write(f"Config checker last ran at {last_check}")

else:
    st.write(f":red[Supplied directory `{dir_string}` not found. Please follow the format below]")
    st.markdown(multi_line)



if runnable:
    if st.button("Run Checker", type="primary"):
        result = run_checker_on_dir(dir_path)
        if result:
            st.badge("Success 🥳", icon=":material/check:", color="green")
            st.subheader("Checker output (also in file `config_checker.log`):")
            with open(dir_path / "config_check.log", 'r') as fin:
                for line in fin.readlines():
                    first_word = line.split(' ')[0]
                    if first_word in fmt_colors.keys():
                        line = f":{fmt_colors[first_word]}[{line}]"
                    st.write(line)
        else:
            st.subheader(":red[Script Failed! 😭 contact Callum]")

st.markdown("-------------")
st.markdown("Source code at [github.com/voto-ocean-knowledge/deployment-yaml](https://github.com/voto-ocean-knowledge/deployment-yaml)")
st.markdown("You can find all of the output yaml files on the server in `data/scripts/deployment_yaml/yaml_from_config`")
