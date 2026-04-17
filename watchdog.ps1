$env:JL_API_KEY = "ljpVQf3s1lYuJP-oPrTKnbbFL7bPBvbzTUx0EH_kC1U"
$env:PYTHONIOENCODING = "utf8"
$logFile = "C:\happy horse\watchdog.log"
$instanceId = "395779"
$sshPort = "11114"

Add-Content $logFile "[$(Get-Date)] Watchdog started. Monitoring instance $instanceId..."

while ($true) {
    Start-Sleep -Seconds 120

    $log = ssh -o StrictHostKeyChecking=no -p $sshPort root@sshe.jarvislabs.ai "tail -n 5 /home/generation_v2.log" 2>&1

    Add-Content $logFile "[$(Get-Date)] Log check: $log"

    if ($log -match "All done") {
        Add-Content $logFile "[$(Get-Date)] SUCCESS! Movie is ready. Downloading..."

        scp -o StrictHostKeyChecking=no -P $sshPort root@sshe.jarvislabs.ai:/home/FINAL_SW1_MOVIE.mp4 "C:\happy horse\FINAL_SW1_MOVIE.mp4"

        Add-Content $logFile "[$(Get-Date)] Download complete! Destroying instance $instanceId..."

        python -c "from jarvislabs.cli.app import main; import sys; sys.argv=['jl', 'destroy', '$instanceId', '--yes']; main()"

        Add-Content $logFile "[$(Get-Date)] Instance destroyed. Job complete! Watchdog exiting."
        break
    }

    if ($log -match "Error" -or $log -match "Traceback") {
        Add-Content $logFile "[$(Get-Date)] ERROR detected in generation log! Check watchdog.log manually."
        break
    }
}
