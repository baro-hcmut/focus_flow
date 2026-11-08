Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

Dim pywPath
pywPath = "C:\Users\nhatb\AppData\Local\Programs\Python\Python314\pythonw.exe"
If Not fso.FileExists(pywPath) Then
    pywPath = "pythonw.exe"
End If

WshShell.Run """" & pywPath & """ """ & scriptDir & "\main.py""", 0, False
