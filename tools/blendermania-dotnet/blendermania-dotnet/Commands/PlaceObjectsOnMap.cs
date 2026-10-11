using GBX.NET;
using GBX.NET.Engines.Game;

namespace blendermania_dotnet;

public class PlaceObjectsOnMap : Map, ICommand
{
    public const string COMMAND_NAME = "place-objects-on-map";
    public bool ShouldOverwrite { get; set; } = false;
    public string MapSuffix { get; set; } = "_modified";
    public bool CleanBlocks { get; set; } = true;
    public bool CleanItems { get; set; } = true;

    public static async Task<int> Execute(string payload)
    {
        var json = File.ReadAllText(payload);
        var map = JsonSerializer.Deserialize<PlaceObjectsOnMap>(json, Constants.CommonJsonSerializerOptions)
            ?? throw new Exception("Invalid json");

        return await map.Run();
    }

    async Task<int> Run()
    {
        if (MapPath is null || MapPath.Length == 0)
        {
            Console.WriteLine("MapPath is not provided");
            return (int)ExitCodes.InvalidPayload;
        }

        try
        {
            var map = Gbx.ParseNode<CGameCtnChallenge>(MapPath);

            // clean up existed data
            if (CleanBlocks) // DOESN'T WORK ATM IN GBX.NET
            {
                if (Blocks.Count > 0 && map.Blocks is not null)
                {
                    //map.Blocks.Clear();
                }
            }

            if (CleanItems)
            {
                map.EmbeddedZipData = [];

                if (map.AnchoredObjects is not null)
                {
                    map.AnchoredObjects.Clear();
                }
            }

            // palce items
            foreach (var item in Items)
            {
                map = item.AddItemToMap(map, Env);
            }

            // palce blocks
            foreach (var block in Blocks) // VERY UNSTABLE
            {
                //map = block.AddBlockToMap(map);
            }

            // save modified map
            var NewPath = MapPath;
            if (!ShouldOverwrite)
            {
                if (MapSuffix.Trim().Count() == 0)
                {
                    MapSuffix = "_modified";
                }

                map.MapName += MapSuffix;

                // change file name
                var dir = Path.GetDirectoryName(NewPath);
                var fn = Path.GetFileNameWithoutExtension(NewPath);
                var ext = Path.GetExtension(NewPath);
                if (fn.ToLower().Contains(".map"))
                {
                    fn = Path.GetFileNameWithoutExtension(fn) + MapSuffix + ".Map";
                }
                else
                {
                    fn = fn + MapSuffix;
                }

                if (dir is null)
                {
                    dir = "";
                }
                NewPath = Path.Combine(dir, fn + ext);
            }

            map.Save(NewPath);

            return (int)ExitCodes.Success;
        }
        catch (Exception err)
        {
            Console.WriteLine("Error: " + err.Message);
            return (int)ExitCodes.GBXError;
        }

    }
}