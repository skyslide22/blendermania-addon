using GBX.NET;
using TM_GenericMapping.Items.FbxGbxConversion;
using TM_GenericMapping.Items.FbxGbxConversion.Serialization;
using TM_GenericMapping.Items.MeshCompilation;
using TM_GenericMapping.Messaging;

namespace blendermania_dotnet;

public class ConvertFbxToGbxPayload
{
    /// <summary>
    /// Required.
    /// </summary>
    public string FbxPath { get; set; } = "";

    /// <summary>
    /// Required.
    /// </summary>
    public string MaterialLibraryPath { get; set; } = "";

    /// <summary>
    /// Required.
    /// </summary>
    public string ItemOutputPath { get; set; } = "";

    /// <summary>
    /// Optional.
    /// </summary>
    public string IconPath { get; set; } = "";

    /// <summary>
    /// Required.
    /// </summary>
    public ItemModel Target { get; set; } = ItemModel.Prefab;

    /// <summary>
    /// Required.
    /// </summary>
    public ItemCompilerOptimization Optimization { get; set; } = ItemCompilerOptimization.PreferNadeoImporterStructure;
}

public class ConvertFbxToGbx : ICommand
{
    public const string COMMAND_NAME = "convert-fbx-to-gbx";

    const string JSON_CONFIG_POSTFIX = ".json";

    public required ConvertFbxToGbxPayload Payload { get; init; }
    async Task<int> Run()
    {
        // create read streams
        var expectedConfigPath = Payload.FbxPath.Replace(".fbx", JSON_CONFIG_POSTFIX);
        using var fbxStream = File.OpenRead(Payload.FbxPath);
        using var configStream = File.OpenRead(expectedConfigPath);
        using var materialLibraryStream = File.OpenRead(Payload.MaterialLibraryPath);
        var materialLibrary = DMaterialLibraryParser.Parse(materialLibraryStream);

        using Stream? iconStream = File.Exists(Payload.IconPath) ?
            File.OpenRead(Payload.IconPath) :
            null;
        string? itemOutputPathOverride = string.IsNullOrWhiteSpace(Payload.ItemOutputPath) ? null : Payload.ItemOutputPath;

        // create conversion input
        using var fbxGbxConversionInput = FbxGbxConversionInput.CreateFromItemConfig(configStream, fbxStream, materialLibrary, iconStream, itemOutputPathOverride);

        // create converter and compile options
        var fbxGbxConverter = new FbxGbxConverter();
        var compileOptions = new CompileOptions()
        {
            Target = Payload.Target,
            Optimization = Payload.Optimization,
        };

        // create item and save it 

        var result = fbxGbxConverter.ConvertToGbxAndSaveItem(fbxGbxConversionInput, compileOptions);
        if (result.IsFailure)
        {
            string msg = result.ErrorCode switch
            {
                ErrorCodes.FbxGbxConverter.FbxParsingError => "Failed to parse FBX file.",
                ErrorCodes.FbxGbxConverter.InvalidItemOutputPath => "Invalid item output path.",
                ErrorCodes.FbxGbxConverter.MissingMaterialConfig => "Missing material configuration.",
                ErrorCodes.FbxGbxConverter.MissingLightConfig => "Missing light configuration.",
                ErrorCodes.FbxGbxConverter.MissingMeshConfig => "Missing mesh configuration.",
                ErrorCodes.FbxGbxConverter.MultipleSocketsNotSupported => "Multiple sockets are not supported.",
                ErrorCodes.FbxGbxConverter.MissingStaticMeshGroup => "Missing static mesh group for lights.",
                ErrorCodes.FbxGbxConverter.MissingLodDistanceConfig => "Missing LOD distance configuration.",
                _ => result.ErrorCode ?? "Unknown error",
            };
            Console.WriteLine($"Error: {msg}");
            return (int)ExitCodes.GBXError;
        }

        return (int)ExitCodes.Success;
    }
        

    public static async Task<int> Execute(string payload)
    {
        ConvertFbxToGbxPayload fbxGbxPayload;
        try
        {
            fbxGbxPayload = JsonSerializer.Deserialize<ConvertFbxToGbxPayload>(payload)!;
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.ToString());
            return (int)ExitCodes.InvalidPayload;
        }
        var convertFbxToGbx = new ConvertFbxToGbx() { Payload = fbxGbxPayload };
        return await convertFbxToGbx.Run();
    }
}
