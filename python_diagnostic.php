<?php
/**
 * Python Environment Diagnostic Script
 * Use this to understand what's available on your shared hosting
 */

header('Content-Type: text/plain');
echo "=== PYTHON ENVIRONMENT DIAGNOSTIC ===\n\n";

// Test different Python commands
$python_commands = [
    'python3',
    'python',
    'python3.9',
    'python3.8',
    'python3.10',
    'python3.11',
    '/usr/bin/python3',
    '/usr/local/bin/python3',
    '/opt/python/bin/python3',
    '/usr/bin/python',
    '/usr/local/bin/python',
    '/home/python/bin/python3',
    '/usr/local/cpanel/3rdparty/bin/python3'
];

echo "1. PYTHON EXECUTABLE DETECTION:\n";
echo str_repeat("-", 50) . "\n";

foreach ($python_commands as $cmd) {
    echo "Testing: $cmd\n";
    
    $which_output = shell_exec("which $cmd 2>&1");
    echo "Which output: " . trim($which_output) . "\n";
    
    $version_output = shell_exec("$cmd --version 2>&1");
    echo "Version: " . trim($version_output) . "\n";
    
    echo "\n";
}

// Check for Python libraries
echo "2. PYTHON LIBRARIES SEARCH:\n";
echo str_repeat("-", 50) . "\n";

$python_lib_paths = [
    '/usr/local/lib/python*',
    '/usr/lib/python*',
    '/opt/python/lib/python*',
    '/home/python/lib/python*'
];

foreach ($python_lib_paths as $path) {
    $libraries = glob($path);
    if (!empty($libraries)) {
        echo "Found Python libraries in: $path\n";
        foreach ($libraries as $lib) {
            echo "  - $lib\n";
        }
    }
}

// Check PATH environment
echo "\n3. ENVIRONMENT VARIABLES:\n";
echo str_repeat("-", 50) . "\n";
echo "PATH: " . (getenv('PATH') ?: 'Not set') . "\n";
echo "PYTHONPATH: " . (getenv('PYTHONPATH') ?: 'Not set') . "\n";
echo "HOME: " . (getenv('HOME') ?: 'Not set') . "\n";
echo "USER: " . (getenv('USER') ?: 'Not set') . "\n";

// Check for yt-dlp
echo "\n4. YT-DLP DETECTION:\n";
echo str_repeat("-", 50) . "\n";

$ytdlp_commands = [
    'yt-dlp',
    '/usr/local/bin/yt-dlp',
    '/usr/bin/yt-dlp',
    'python3 -m yt_dlp',
    '/usr/local/bin/python3 -m yt_dlp'
];

foreach ($ytdlp_commands as $cmd) {
    echo "Testing: $cmd\n";
    $output = shell_exec("$cmd --version 2>&1");
    echo "Output: " . trim($output) . "\n\n";
}

// Check for pip
echo "5. PIP DETECTION:\n";
echo str_repeat("-", 50) . "\n";

$pip_commands = [
    'pip',
    'pip3',
    'python3 -m pip',
    '/usr/local/bin/pip3'
];

foreach ($pip_commands as $cmd) {
    echo "Testing: $cmd\n";
    $output = shell_exec("$cmd --version 2>&1");
    echo "Output: " . trim($output) . "\n\n";
}

// Check system info
echo "6. SYSTEM INFORMATION:\n";
echo str_repeat("-", 50) . "\n";
echo "OS: " . php_uname() . "\n";
echo "PHP Version: " . phpversion() . "\n";
echo "Server Software: " . ($_SERVER['SERVER_SOFTWARE'] ?? 'Unknown') . "\n";
echo "Document Root: " . ($_SERVER['DOCUMENT_ROOT'] ?? 'Unknown') . "\n";

// Check common Python module locations
echo "\n7. MODULE SEARCH:\n";
echo str_repeat("-", 50) . "\n";

$module_paths = [
    '/usr/local/lib/python3.9/site-packages',
    '/usr/local/lib/python3.8/site-packages',
    '/usr/lib/python3/dist-packages',
    '/home/python/lib/python3.9/site-packages'
];

foreach ($module_paths as $path) {
    if (is_dir($path)) {
        echo "Found modules in: $path\n";
        $modules = glob($path . '/*');
        if (!empty($modules)) {
            echo "  Sample modules:\n";
            foreach (array_slice($modules, 0, 10) as $module) {
                echo "    - " . basename($module) . "\n";
            }
        }
    }
}

// Test if we can create a simple Python script
echo "\n8. PYTHON EXECUTION TEST:\n";
echo str_repeat("-", 50) . "\n";

$test_script = '/tmp/test_python.py';
$python_code = '#!/usr/bin/env python3
import sys
print("Python version:", sys.version)
print("Python path:", sys.path)
try:
    import yt_dlp
    print("yt-dlp is available")
except ImportError:
    print("yt-dlp is not available")
';

if (file_put_contents($test_script, $python_code)) {
    echo "Created test script: $test_script\n";
    
    $python_executables = ['python3', 'python', '/usr/local/bin/python3'];
    foreach ($python_executables as $python) {
        echo "Testing with $python:\n";
        $output = shell_exec("$python $test_script 2>&1");
        echo "Output: " . trim($output) . "\n\n";
    }
    
    // Clean up
    unlink($test_script);
} else {
    echo "Could not create test script (write permissions issue)\n";
}

// Suggestions based on findings
echo "\n9. RECOMMENDATIONS:\n";
echo str_repeat("-", 50) . "\n";

$has_python_libs = !empty(glob('/usr/local/lib/python*'));
$has_python_exec = false;

foreach ($python_commands as $cmd) {
    $which_output = shell_exec("which $cmd 2>&1");
    if (!empty($which_output) && strpos($which_output, 'no ') === false) {
        $has_python_exec = true;
        break;
    }
}

if ($has_python_libs && !$has_python_exec) {
    echo "🔍 ISSUE IDENTIFIED: Python libraries exist but executable not in PATH\n";
    echo "\nPossible solutions:\n";
    echo "1. Contact your hosting provider to add Python to PATH\n";
    echo "2. Ask about enabling Python CGI or WSGI support\n";
    echo "3. Request installation of yt-dlp via pip\n";
    echo "4. Consider upgrading to a hosting plan with Python support\n";
} elseif (!$has_python_libs && !$has_python_exec) {
    echo "❌ ISSUE: No Python installation found\n";
    echo "\nYou need to:\n";
    echo "1. Contact your hosting provider about Python support\n";
    echo "2. Consider switching to a Python-friendly hosting provider\n";
    echo "3. Use a VPS or dedicated server for full Python support\n";
} elseif ($has_python_exec) {
    echo "✅ Python executable found! Check yt-dlp installation\n";
    echo "\nNext steps:\n";
    echo "1. Install yt-dlp: pip install yt-dlp\n";
    echo "2. Test the main application\n";
}

echo "\n=== END OF DIAGNOSTIC ===\n";
?> 