using GBX.NET;
using GBX.NET.Engines.Game;

namespace blendermania_dotnet
{
    public class Block
    {
        public string? Name { get; set; }
        public Int3 Position { get; set; } = new Int3();
        public Direction Dir { get; set; } = Direction.North;
        public CGameCtnChallenge AddBlockToMap(CGameCtnChallenge Map)
        {
            if (Name is null)
            {
                throw new Exception("Null block Name");
            }

            Map.PlaceBlock(new Ident(Name), Position, Dir);
            return Map;
        }
    }
}