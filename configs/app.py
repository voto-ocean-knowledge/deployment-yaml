from pathlib import Path
import streamlit as st
from reader import run_checker_on_dir

runnable = False
fmt_colors = {
    'WARNING': 'orange',
    'ERROR': 'red',
}

st.title("Config Checker for SeaExplorer")


dir_string = st.text_input(r'Input directory path ')
if "\\" in dir_string:
    dir_string = dir_string.replace("\\", "/")
    if dir_string[:4] != "/mnt":
        dir_base, dir_append = dir_string.split('docs/')
        dir_string = "/mnt/docs/" + dir_append

dir_path = Path(dir_string)
if dir_path.is_file():
    dir_path = dir_path.parent

multi_line = r'''Please enter a directory with config files. Acceptable formats include:  
- `/mnt/docs/1_Operations/Missions/23_Phycoglider_2/SEA077_PLD094/SEA077_M44`  
- `\docs\1_Operations\Missions\07_SAMBA_05\02_SAMBA_05_002\SEA076_PLD093\YYYYMMDD_M41`  
     '''

if dir_path == Path(""):
    st.markdown(multi_line)
elif dir_path.is_dir():
    file_paths = dir_path.glob("*")
    files = [file_path.name for file_path in file_paths]
    st.write("The selected directory is ", dir_path)
    st.write("The directory contains ", files)
    missing_files = {"sea.cfg", "sea.msn", "seapayload.cfg"}.difference(files)
    if missing_files:
        st.write(f":red[Supplied directory is missing config files: {missing_files}]")
    else:
        runnable = True
    if "config_check.log" in files:
        print("one")
        with open(dir_path / "config_check.log") as fin:
            for line in fin.readlines():
                if "START" in line:
                    print("two")
                    last_check = line.split('check at ')[1][:20]
                    print(last_check)
                    if last_check[:2] == "20":
                        print("three")
                        st.write(f":green[ Config checker last ran at {last_check}]")

else:
    st.write(f":red[Supplied directory `{dir_string}` not found. Please follow the format below]")
    st.markdown(multi_line)
    print(dir_path)



if runnable:
    if st.button("Run Checker", type="primary"):
        result = run_checker_on_dir(dir_path)
        if result:
            st.badge("Success", icon=":material/check:", color="green")
            st.subheader("Checker output (also in file `config_checker.log`):")
            with open(dir_path / "config_check.log", 'r') as fin:
                for line in fin.readlines():
                    first_word = line.split(' ')[0]
                    if first_word in fmt_colors.keys():
                        line = f":{fmt_colors[first_word]}[{line}]"
                    st.write(line)
        else:
            st.subheader(":red[Script Failed! :( contact Callum]")

st.markdown("-------------")
st.markdown("Source code at [github.com/voto-ocean-knowledge/deployment-yaml](https://github.com/voto-ocean-knowledge/deployment-yaml)")
