Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
rootDir = fso.GetParentFolderName(scriptDir)
WshShell.CurrentDirectory = rootDir

Dim pywPath
pywPath = "C:\Users\nhatb\AppData\Local\Programs\Python\Python314\pythonw.exe"
If Not fso.FileExists(pywPath) Then
    pywPath = "pythonw.exe"
End If

WshShell.Run """" & pywPath & """ """ & rootDir & "\main.py""", 0, False
