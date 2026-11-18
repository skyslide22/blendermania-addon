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


