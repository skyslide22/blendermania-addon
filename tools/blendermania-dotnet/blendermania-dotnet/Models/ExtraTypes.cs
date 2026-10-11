using GBX.NET;

namespace blendermania_dotnet
{
    public class Vector3 {
        public float X { get; set; }
        public float Y { get; set; }
        public float Z { get; set; }
        public Vec3 ToGBXNetVec3()
        {
            return new Vec3(X, Y, Z);
        }
    }
}
