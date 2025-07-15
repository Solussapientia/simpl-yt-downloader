<?php
echo "<h1>Python Detection Test</h1>";

$python_commands = [
    'python3',
    'python',
    'python3.9',
    'python3.8',
    'python3.7',
    '/usr/bin/python3',
    '/usr/bin/python',
    '/usr/local/bin/python3',
    '/opt/python/bin/python3'
];

foreach ($python_commands as $cmd) {
    echo "<h3>Testing: $cmd</h3>";
    $output = shell_exec("which $cmd 2>&1");
    echo "<p>Which output: " . htmlspecialchars($output) . "</p>";
    
    $version = shell_exec("$cmd --version 2>&1");
    echo "<p>Version: " . htmlspecialchars($version) . "</p>";
    
    echo "<hr>";
}

echo "<h2>Available Python-related files:</h2>";
$python_files = shell_exec("find /usr -name '*python*' 2>/dev/null | head -20");
echo "<pre>" . htmlspecialchars($python_files) . "</pre>";

echo "<h2>Environment PATH:</h2>";
echo "<pre>" . htmlspecialchars($_ENV['PATH'] ?? 'Not set') . "</pre>";
?> 