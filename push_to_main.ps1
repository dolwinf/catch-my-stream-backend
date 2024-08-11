# Check if comment is provided
if ($args.Count -eq 0) {
    Write-Host "No comment provided."
    exit
}

$inputString = $args[0]

git add .
git commit -m $inputString
git push origin main