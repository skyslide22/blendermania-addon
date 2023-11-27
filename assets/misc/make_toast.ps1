[cmdletBinding()]
Param(
    [Parameter(Mandatory, Position = 0)][String] $Title,
    [Parameter(Mandatory, Position = 1)][String] $Message,
    [Parameter(Mandatory, Position = 2)][String] $Icon,
    [Parameter(Mandatory, Position = 3)][String] $BaloonIcon,
    [Parameter(Mandatory, Position = 4)][Int]    $Duration
)

[void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
$objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
$objNotifyIcon.Icon = $Icon
$objNotifyIcon.BalloonTipIcon = $BaloonIcon # None, Info, Warning, Error
$objNotifyIcon.BalloonTipText = $Message
$objNotifyIcon.BalloonTipTitle = $Title
$objNotifyIcon.Visible = $True
$objNotifyIcon.ShowBalloonTip($Duration)

Start-Sleep 500