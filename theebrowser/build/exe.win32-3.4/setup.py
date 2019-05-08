from cx_Freeze import setup , Executable

setup(name ='urlParse',version='0.1',description='parse stuff',executables=[Executable("browser.py")])