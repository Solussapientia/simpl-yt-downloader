<?php
// Test PHP file to check server status
echo "<h1>Server Test</h1>";
echo "<p>PHP is working!</p>";
echo "<p>Server info:</p>";
echo "<ul>";
echo "<li>PHP Version: " . phpversion() . "</li>";
echo "<li>Server Software: " . $_SERVER['SERVER_SOFTWARE'] . "</li>";
echo "<li>Document Root: " . $_SERVER['DOCUMENT_ROOT'] . "</li>";
echo "<li>Current Directory: " . getcwd() . "</li>";
echo "</ul>";

echo "<h2>Python Test</h2>";
$python_test = shell_exec('python3 --version 2>&1');
echo "<p>Python3 Version: " . $python_test . "</p>";

$pip_test = shell_exec('pip3 list 2>&1');
echo "<p>Python packages installed:</p>";
echo "<pre>" . $pip_test . "</pre>";

echo "<h2>File Structure</h2>";
$files = scandir('.');
echo "<ul>";
foreach($files as $file) {
    if ($file != '.' && $file != '..') {
        echo "<li>" . $file . "</li>";
    }
}
echo "</ul>";
?> 