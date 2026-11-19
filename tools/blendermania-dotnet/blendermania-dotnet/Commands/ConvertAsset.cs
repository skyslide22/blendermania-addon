using TM_GenericMapping.Items.GbxConversion;
using TM_GenericMapping.Messaging;

public class ConvertAssetPayload
{
    public AssetType AssetType { get; set; }

    public string AssetPath { get; set; } = "";
    public BitmapConfig? BitmapPayload { get; set; }
}
public enum AssetType
{
    Bitmap,
}

public class ConvertAsset : ICommand
{
    public const string COMMAND_NAME = "convert-asset";
    const string JSON_CONFIG_POSTFIX = ".json";

    static readonly JsonSerializerOptions PayloadOptions = new()
    {
        Converters =
        {
            new System.Text.Json.Serialization.JsonStringEnumConverter(),
            new blendermania_dotnet.Vec2ArrayConverter(),
            new blendermania_dotnet.ColorArrayConverter(),
        },
    };

    public required ConvertAssetPayload Payload { get; init; }

    async Task<int> Run()
    {
        switch (Payload.AssetType)
        {
            case AssetType.Bitmap:
                if (Payload.BitmapPayload is null)
                {
                    Console.WriteLine("BitmapPayload is missing.");
                    return (int)ExitCodes.InvalidPayload;
                }
                var converter = new CPlugBitmapConverter();
                var result = converter.ConvertAndSave(Payload.BitmapPayload!, Payload.AssetPath);
                if (result.IsFailure)
                {
                    Console.WriteLine($"Failed to convert bitmap: {result.ErrorCode}");
                    return (int)ExitCodes.UnknownError;
                }
                break;


            default:
                throw new NotImplementedException($"Asset type {Payload.AssetType} is not implemented.");
        }
        return (int)ExitCodes.Success;
    }
        

 
    public static async Task<int> Execute(string payload)
    {
        ConvertAssetPayload assetPayload;
        try
        {
            assetPayload = JsonSerializer.Deserialize<ConvertAssetPayload>(payload, PayloadOptions)!;
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.ToString());
            return (int)ExitCodes.InvalidPayload;
        }
        try
        {
            var convertAsset = new ConvertAsset() { Payload = assetPayload };
            return await convertAsset.Run();
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.ToString());
            return (int)ExitCodes.UnknownError;
        }
    }

}



/// <summary>"convert-assets": many bitmaps in one process (default asset library), payload = { "Assets": [ConvertAssetPayload, ...] }.
/// Prints "PROGRESS: i/n" and one "FAILED: path: reason" line per failure; exit code Success only if all converted.</summary>
public class ConvertAssetsBatch : ICommand
{
    public const string COMMAND_NAME = "convert-assets";

    class Payload { public List<ConvertAssetPayload> Assets { get; set; } = []; }

    static readonly JsonSerializerOptions PayloadOptions = new()
    {
        Converters =
        {
            new System.Text.Json.Serialization.JsonStringEnumConverter(),
            new blendermania_dotnet.Vec2ArrayConverter(),
            new blendermania_dotnet.ColorArrayConverter(),
        },
    };

    public static Task<int> Execute(string payload)
    {
        Payload input;
        try
        {
            input = JsonSerializer.Deserialize<Payload>(File.Exists(payload) ? File.ReadAllText(payload) : payload, PayloadOptions)!;
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.ToString());
            return Task.FromResult((int)ExitCodes.InvalidPayload);
        }

        var converter = new CPlugBitmapConverter();
        int failed = 0, done = 0, total = input.Assets.Count;
        foreach (var asset in input.Assets)
        {
            try
            {
                if (asset.AssetType != AssetType.Bitmap || asset.BitmapPayload is null)
                    throw new InvalidDataException("only bitmaps with BitmapPayload are supported");
                Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(asset.AssetPath))!);
                var result = converter.ConvertAndSave(asset.BitmapPayload, asset.AssetPath);
                if (result.IsFailure)
                    throw new InvalidDataException(result.ErrorCode.ToString());
            }
            catch (Exception ex)
            {
                failed++;
                Console.WriteLine($"FAILED: {asset.AssetPath}: {ex.Message}");
            }
            done++;
            if (done % 20 == 0 || done == total)
                Console.WriteLine($"PROGRESS: {done}/{total}");
        }
        Console.WriteLine($"SUCCESS: {total - failed}/{total} converted");
        return Task.FromResult(failed == 0 ? (int)ExitCodes.Success : (int)ExitCodes.UnknownError);
    }
}
