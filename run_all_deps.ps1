#######################################################################
# run_all_deps.ps1
# Runs ComputeFileDependencies (function 231) for all filelists.
# - Creates per-filelist config_deps_XXX.xml files in $ConfigDir
# - Maps each filelist to its settings.xml
# - Skips already-analyzed models (incremental)
# - Outputs NDJSON files in $OutDir
#######################################################################

param(
    [string]$OutDir    = "C:\HEC\deps",
    [string]$LibDir    = "C:\git\exchange_core\build_irt\bin\RelWithDebInfo",
    [string]$ConfigDir = "C:\HEC",
    [int]   $Process   = 40,
    [switch]$DryRun           # Print commands without running
)

$FilelistDir = "C:\git\exchange_core\exchange\admin\QA\Filelist"
$QAConfigDir = "C:\git\exchange_core\exchange\admin\QA\Configuration"
$HEC_EXE     = Join-Path $LibDir "HoopsExchangeChecker.exe"

# ── Filelist name → Configuration subdirectory (relative to $QAConfigDir) ──
# Each entry maps filelist_<KEY>.txt → <VALUE>/settings.xml
$Mapping = [ordered]@{
    # ── Import formats ──
    "3DS"                        = "Import/3DS"
    "3DXML"                      = "Import/3DXML"
    "3DXML_PMI_Views"            = "Import/3DXML/PMI_Views"
    "3MF"                        = "Import/3MF"
    "ACIS"                       = "Import/ACIS"
    "CATIA_V4"                   = "Import/CATIA_V4"
    "CATIA_V5"                   = "Import/CATIA_V5"
    "CATIA_V5_Drawings"          = "Import/CATIA_V5/Drawings"
    "CATIA_V5_PMI_Views"         = "Import/CATIA_V5/PMI_Views"
    "CATIA_V5_UseMaterialRendering" = "Import/CATIA_V5/UseMaterialRendering"
    "CGR"                        = "Import/CGR"
    "COLLADA"                    = "Import/COLLADA"
#    "DGN"                        = "Import/DGN"
    "DWF"                        = "Import/DWF"
    "DWG"                        = "Import/DWG"
    "DWG_Drawings"               = "Import/DWG/Drawings"
    "DWG_Drawings_Model_Info"    = "Import/DWG/Drawings/Model_Info"
    "FBX"                        = "Import/FBX"
    "GLTF"                       = "Import/GLTF"
    "HSF"                        = "Import/HSF"
    "IDEAS"                      = "Import/IDEAS"
    "IFC"                        = "Import/IFC"
    "IFC_Boolean_Operations"     = "Import/IFC"
    "IFC_HideWireframe"          = "Import/IFC/HideWireframe"
    "IGES"                       = "Import/IGES"
    "INVENTOR"                   = "Import/INVENTOR"
    "INVENTOR_DontUseFileTess"   = "Import/INVENTOR/DontUseFileTess"
    "JT"                         = "Import/JT"
    "JT_PMI_Views"               = "Import/JT/PMI_Views"
    "JT_ULP"                     = "Import/JT/ULP"
    "NW"                         = "Import/NW"
    "NX"                         = "Import/NX"
    "NX_Fit_All"                 = "Import/NX/Fit_All"
    "NX_PMI_Views"               = "Import/NX/PMI_Views"
    "OBJ"                        = "Import/OBJ"
    "PARASOLID"                  = "Import/PARASOLID"
    "PDF"                        = "Import/PDF"
    "PROE"                       = "Import/PROE"
    "PROE_Boolean_Operations"    = "Import/PROE/Boolean_Operations"
    "PROE_Family_Tables"         = "Import/PROE/Family_Tables_0"
    "PROE_Flexible_Parts"        = "Import/PROE/Flexible_Parts"
    "PROE_Hidden_Skeleton"       = "Import/PROE/Hidden_Skeleton"
    "PROE_PMI_Views"             = "Import/PROE/PMI_Views"
    "REVIT"                      = "Import/REVIT/3D"
    "REVIT_3D_PMI_Views"         = "Import/REVIT/3D/PMI_Views"
    "REVIT_3D_PhysicalProperties"= "Import/REVIT/3D/PhysicalProperties_Computed"
    "RHINO"                      = "Import/RHINO"
    "SE"                         = "Import/SE"
    "SE_Configurations"          = "Import/SE/Configurations"
    "SLW"                        = "Import/SLW"
    "SLW_Configurations"         = "Import/SLW/Configurations"
    "SLW_PMI_Views"              = "Import/SLW/PMI_Views"
    "STEP"                       = "Import/STEP"
    "STEPXML"                    = "Import/STEPXML"
    "STEP_Heal_Orientations"     = "Import/STEP/Heal_Orientations"
    "STEP_PMI_Views"             = "Import/STEP/PMI_Views"
    "STL"                        = "Import/STL"
    "U3D"                        = "Import/U3D"
    "VDA"                        = "Import/VDA"
    "VRML"                       = "Import/VRML"
    "XML"                        = "Import/XML"

    # ── Export formats ──
    "Export_3MF"                         = "Export/3MF"
    "Export_ACIS"                        = "Export/ACIS"
    "Export_FBX"                         = "Export/FBX/Binary"
    "Export_FBX_Model_Info"              = "Export/FBX/Binary_Model_Info"
    "Export_GLTF"                        = "Export/GLTF"
    "Export_GLTF_Model_Info"             = "Export/GLTF/Model_Info"
    "Export_HTML"                        = "Export/HTML"
    "Export_HTML_with_PDF"               = "Export/HTML/with_PDF"
    "Export_IFC"                         = "Export/IFC"
    "Export_IFC_Model_Info"              = "Export/IFC/Model_Info"
    "Export_IGES"                        = "Export/IGES"
    "Export_JT"                          = "Export/JT/9.5"
    "Export_JT_Model_Info"               = "Export/JT/9.5/Model_Info"
    "Export_JT_tessellation"             = "Export/JT/9.5/Tessellation"
    "Export_OBJ"                         = "Export/OBJ"
    "Export_OBJ_Model_Info"              = "Export/OBJ/Model_Info"
    "Export_PARASOLID"                   = "Export/PARASOLID"
    "Export_PARASOLID_Binary"            = "Export/PARASOLID/Binary"
    "Export_PARASOLID_T2PKP"             = "Export/PARASOLID/T2PKP"
    "Export_PARASOLID_T2PKP_Healing_Sew" = "Export/PARASOLID/T2PKP_Healing_Sew"
    "Export_PARASOLID_Write_Tessellation"= "Export/PARASOLID/Write_Tessellation"
    "Export_PDF"                         = "Export/PDF"
    "Export_PMI_Views"                   = "Export/JT/9.5/PMI_Views"
    "Export_PRC"                         = "Export/PRC"
    "Export_PRC_Markup_Definition"       = "Export/PRC/Markup_Definition"
    "Export_PRC_Markup_Linked_Item"      = "Export/PRC/Markup_Linked_Item"
    "Export_PRC_Model_Info"              = "Export/PRC/Model_Info"
    "Export_SCS"                         = "Export/SCS"
    "Export_STEP"                        = "Export/STEP/AP214"
    "Export_STEP_AP242_Markup_Definition"       = "Export/STEP/AP242/Markup_Definition"
    "Export_STEP_AP242_Markup_Linked_Item"      = "Export/STEP/AP242/Markup_Linked_Item"
    "Export_STEP_AP242_Model_Info"              = "Export/STEP/AP242/Model_Info"
    "Export_STL"                         = "Export/STL"
    "Export_STL_tessellation"            = "Export/STL/Accurate"
    "Export_U3D"                         = "Export/U3D"
    "Export_VRML"                        = "Export/VRML"
    "Export_X3D"                         = "Export/X3D"
    "Export_XML"                         = "Export/XML"

    # ── Dump / Read / Special ──
    "Dump_Constraints"                   = "Dump/Constraints"
    "Dump_DraftingRow_TextsInBoxes_RTF"  = "Dump/DraftingRow_TextsInBoxes_RTF"
    "Dump_Features"                      = "Dump/Features"
    "Dump_Geometry_Info"                 = "Dump/Geometry_Info"
    "Dump_Global_Info"                   = "Dump/Global_Info"
    "Dump_Markup_Definition"             = "Dump/Markup_Definition"
    "Dump_Markup_Linked_Item"            = "Dump/Markup_Linked_Item"
    "Dump_Model_Info"                    = "Dump/Model_Info"
    "Dump_Rigid_Attributes"              = "Dump/Rigid_Attributes"
    "Read_Active_Filter"                 = "Read/Active_Filter"
    "Read_Attributes"                    = "Read/Attributes"
    "Read_Construction_And_References"   = "Read/Construction_And_References"
    "Read_Features"                      = "Read/Features"
    "Read_Geom_Only"                     = "Read/Geom_Only"
    "Read_Hidden_Objects"                = "Read/Hidden_Objects"
    "Read_Tess_Only"                     = "Read/Tess_Only"
    "Check_Features"                     = "CheckFeatures"
    "Check_Prc_Id_Entity_Map_x64"        = "CheckPrcIdEntityMap"
    "Accurate_Tessellation"              = "Tessellation/Accurate"
    "CopyAndAdapt"                       = "Copy_And_Adapt"
    "DeepCopy"                           = "DeepCopy"
    "HLR"                                = "HLR"
    "Incremental_Load"                   = "Incremental_Load"
    "NRT_Big_Files"                      = "NRT"
    "One_File_Per_Extension"             = "One_File_Per_Extension"
    "Phys_Props"                         = "Phys_Props"
    "Phys_Props_Include_Hidden_RIs"      = "Phys_Props/Include_Hidden_RIs"
    "Referenced_Bugs"                    = "Referenced_Bugs"
    "Serialization"                      = "Serialization/Basic"
    "Sew"                                = "Sew"
    "Sew_AdaptAndReplace"                = "Sew/Adapt_And_Replace"
    "Sew_AdaptAndReplace_CheckError"     = "Sew/Adapt_And_Replace/CheckError"
    "Sew_Copy_And_Adapt"                 = "Sew/Copy_And_Adapt"
    "Sew_Markup_Linked_Item"             = "Sew/Markup_Linked_Item"
    "Shattered"                          = "Shattered"
    "SimplifyModelfileCurveAndSurface"   = "SimplifyModelFileCurveAndSurface"
    "Tessellation"                       = "Tessellation/Standard_LOD_0"
    "UUIDs"                              = "UUIDs"
    "Unsupported_Versions"               = "Unsupported_versions"
}

# ── Filelists to skip (Linux, macOS, iOS, Android, or special-purpose) ──
$Skip = @(
    "3MF_Linux", "CATIA_V5_Linux_x64", "CATIA_V5_Constraints",
    "DWF_Linux", "Dump_Features_Linux", "Dump_Features_macOS",
    "Dump_Model_Info_Linux", "Dump_Model_Info_macOS",
    "DumpIFCRelationship",
    "Export_3MF_linux", "Export_3MF_macOS",
    "Export_FBX_linux", "Export_FBX_macOS",
    "Export_OBJ_linux",
    "Export_PRC_Model_Info_Linux",
    "Export_STEP_AP242_Markup_Linked_Item_Linux",
    "Export_Quick_Export_Linux",
    "Incremental_Load_Linux",
    "INVENTOR_linux",
    "One_File_Per_Extension_Linux", "One_File_Per_Extension_macOS",
    "Phys_Props_Linux", "Phys_Props_macOS",
    "Read_Attributes_macOS",
    "Sample_CAD_Files", "Sample_CAD_Files_macOS",
    "Sample_results", "Sample_results_PDF", "Sample_results_Screenshots",
    "Serialization_macOS",
    "UUIDs_Linux", "Unsupported_Versions_macOS",
    "iOS", "Android",
    "Quick", "Quick_Export",
    "Lousy_files",
    "Automate", "AdaptAndReplace_OpenMind", "OpenMind",
    "ProgressBar_AdaptAndReplace", "ProgressBar_Sew",
    "ProgressBar_T2PKP", "ProgressBar_T2PKP_MP",
    "Texture", "PRC",
    "Export_PARASOLID_MP"
)

########################################################################
# Helper: create a config_deps_XXX.xml file
########################################################################
function New-DepsConfig([string]$Name, [string]$ConfigPath) {
    if (Test-Path $ConfigPath) { return }
    $OutputFile = "filelist_${Name}.txt.deps.ndjson"
    $xml = @"
<A3DLibChecker LoadFromFileDisabled="true">
  <Process>
    <Function value="231" option="OutputFile=$OutputFile"/>
  </Process>
</A3DLibChecker>
"@
    Set-Content -Path $ConfigPath -Value $xml -Encoding UTF8
    Write-Host "  Created: $ConfigPath" -ForegroundColor DarkGray
}

########################################################################
# Main
########################################################################
if (!(Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

$total    = 0
$skipped  = 0
$errors   = @()
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " ComputeFileDependencies - batch runner" -ForegroundColor Cyan
Write-Host " OutDir   : $OutDir" -ForegroundColor Cyan
Write-Host " LibDir   : $LibDir" -ForegroundColor Cyan
Write-Host " Process  : $Process" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($entry in $Mapping.GetEnumerator()) {
    $name       = $entry.Key
    $configSub  = $entry.Value
    $filelist   = Join-Path $FilelistDir "filelist_${name}.txt"
    $settings   = Join-Path $QAConfigDir "$configSub\settings.xml"
    $configFile = Join-Path $ConfigDir   "config_deps_${name}.xml"

    # ── Validate paths ──
    if (!(Test-Path $filelist)) {
        Write-Host "  SKIP $name - filelist not found: $filelist" -ForegroundColor Yellow
        $skipped++
        continue
    }
    if (!(Test-Path $settings)) {
        Write-Host "  SKIP $name - settings not found: $settings" -ForegroundColor Yellow
        $skipped++
        continue
    }

    # ── Create config file if needed ──
    New-DepsConfig -Name $name -ConfigPath $configFile

    $total++
    Write-Host "[$total] $name" -ForegroundColor Green -NoNewline
    Write-Host " ($configSub)" -ForegroundColor DarkGray

    $cmd = @(
        $HEC_EXE,
        "-filelist", $filelist,
        "-config",   $configFile,
        "-out",      $OutDir,
        "-settings", $settings,
        "-libdir",   $LibDir,
        "-process",  $Process
    )

    if ($DryRun) {
        Write-Host "  CMD: $($cmd -join ' ')" -ForegroundColor DarkGray
    } else {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        & $HEC_EXE `
            -filelist $filelist `
            -config   $configFile `
            -out      "$OutDir\" `
            -settings $settings `
            -libdir   $LibDir `
            -process  $Process
        $sw.Stop()
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            Write-Host "  ERROR: exit code $exitCode" -ForegroundColor Red
            $errors += $name
        } else {
            Write-Host "  Done in $([math]::Round($sw.Elapsed.TotalSeconds, 1))s" -ForegroundColor DarkGray
        }
    }
}

$stopwatch.Stop()
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Summary" -ForegroundColor Cyan
Write-Host "  Total runs : $total" -ForegroundColor Cyan
Write-Host "  Skipped    : $skipped" -ForegroundColor Cyan
Write-Host "  Errors     : $($errors.Count)" -ForegroundColor $(if ($errors.Count -gt 0) { "Red" } else { "Cyan" })
if ($errors.Count -gt 0) {
    Write-Host "  Failed     : $($errors -join ', ')" -ForegroundColor Red
}
Write-Host "  Total time : $([math]::Round($stopwatch.Elapsed.TotalMinutes, 1)) min" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
