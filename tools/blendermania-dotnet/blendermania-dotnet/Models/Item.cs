using System.Text.Json.Serialization;
using GBX.NET;
using GBX.NET.Engines.Game;
using static GBX.NET.Engines.Game.CGameCtnAnchoredObject;

namespace blendermania_dotnet
{
    public class Item
    {
        public string? Name { get; set; }
        public string? Path { get; set; }
        public Vector3 Position { get; set; } = new Vector3();
        public Vector3 Rotation { get; set; } = new Vector3();
        public Vector3 Pivot { get; set; } = new Vector3();

        [JsonConverter(typeof(EPhaseOffsetConverter))]
        public EPhaseOffset? AnimPhaseOffset { get; set; }

        [JsonConverter(typeof(DifficultyColorConverter))]
        public DifficultyColor? DifficultyColor { get; set; }

        [JsonConverter(typeof(LightmapQualityConverter))]
        public LightmapQuality? LightmapQuality { get; set; }

        public CGameCtnChallenge AddItemToMap(CGameCtnChallenge Map, string Env)
        {
            if (Path is null || Name is null)
            {
                throw new Exception("Null Path or Name");
            }


            if (Name.Contains("/Items/"))
            {
                var parts = Name.Split("/Items/");
                Name = string.Join("/", parts.Skip(1).Take(parts.Length).ToArray());
            }

            Console.WriteLine($"Placing item: {Name} at {Position.X}, {Position.Y}, {Position.Z}");

            var id = new Id(Env);
            if (Env == "Stadium2020")
            {
                id = new Id(26);
            }

            // add anchor to the item
            var item = Map.PlaceAnchoredObject(
                new Ident(Name.Replace("/", @"\"), id, "Blendermania"),
                Position.ToGBXNetVec3(),
                Rotation.ToGBXNetVec3(),
                Pivot.ToGBXNetVec3()
            );


            item.AnimPhaseOffset = AnimPhaseOffset ?? EPhaseOffset.None;
            item.Color = DifficultyColor ?? GBX.NET.DifficultyColor.Default;
            item.LightmapQuality = LightmapQuality ?? GBX.NET.LightmapQuality.Normal;

            return Map;
        }

        public CGameCtnMacroBlockInfo AddItemToMacroblock(CGameCtnMacroBlockInfo Macro)
        {
            if (Path is null || Name is null)
            {
                throw new Exception("Null Path or Name or Position");
            }

            if (Macro.ObjectSpawns is not null)
            {
                var obj = new CGameCtnMacroBlockInfo.ObjectSpawn();
                obj.ItemModel = new Ident(Name.Replace("Items/", "").Replace("/", @"\"), new Id(26), "Blendermania");
                obj.AbsolutePositionInMap = Position.ToGBXNetVec3();
                obj.PitchYawRoll = Rotation.ToGBXNetVec3();
                obj.PivotPosition = Pivot.ToGBXNetVec3();

                Macro.ObjectSpawns.Add(obj);
            }

            return Macro;
        }
    }
}